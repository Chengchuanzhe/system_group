import datetime

from django.contrib.auth import authenticate,login,logout
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, StreamingHttpResponse
from django.contrib.auth.models import User
from app01 import models
from app01.loaduser import load_user_list
import os
from my_class.settings import BASE_DIR
import json
import zipfile
# Create your views here.

def log_in(request):
    return render(request,'login.html')

def log_out(request):
    logout(request)
    return HttpResponseRedirect('/login/')

def user(request):
    if request.method == 'GET':
        return render(request, 'login.html')
    else:
        uname = request.POST.get("uname", "")
        pwd = request.POST.get("pwd", "")
        # print(uname,pwd)
        user = authenticate(request, username=uname, password=pwd)
        if user is not None:
            # 自带的登录功能
            login(request,user)
            # 取得数据库中的学生，这里的name是真实的姓名
            if models.UserProfile.objects.filter(user=user).count() == 0 and user.is_superuser:
                models.UserProfile.objects.create(user=user, name=user.username, gender='M', type='T')
            user = models.UserProfile.objects.filter(user=user)[0]
            # 暂时把数据库中的用户添加到session中，如果后期不用就删掉
            request.session['loginUserName'] = user.name
            # 跳转分支
            if user.type == u'T':
                return HttpResponseRedirect('/teacherCourseList/')
            else:
                return HttpResponseRedirect('/studentCourseList/')
                # return HttpResponse('登录成功')
            # login(request, user)
            # return redirect("/")
        else:
            return HttpResponse("账户或密码不正确！")

# 学生端：通过课程的号码和名字找到对应的作业列表
def studentGetTaskByCoursename(request,courseNumber, coursename):
    if request.user.username:
        course = models.Course.objects.filter(courseNumber=courseNumber, courseName=coursename)[0]
        tasks = models.Task.objects.filter(courseBelongTo=course)
        tasks = [task for task in tasks if task.display == u'Y']
        judge_list = []
        for task in tasks:
            if models.Homework.objects.filter(user = request.user.profile, task = task):
                homework = models.Homework.objects.filter(user=request.user.profile, task=task).first()
                homework_name = homework.filePath.split('\\')[-1]
                judge_list.append(homework_name)
            else:
                judge_list.append('False')
        tasks = zip(tasks, judge_list)
        return render(request, 'studentTasks.html', {'task': tasks})
    else:
        return HttpResponseRedirect('/login/')

# 老师端：作业/任务界面
def teacherGetTaskByCoursename(request,courseNumber, coursename):
    if request.user.username:
        course = models.Course.objects.filter(courseNumber=courseNumber, courseName=coursename)[0]
        # 选了这门课的学生数量
        selectCourseStudentList = course.members.filter(type=u'S')
        # 这门课中的作业列表
        tasks = models.Task.objects.filter(courseBelongTo=course, display=u'Y')
        tasks = [task for task in tasks]
        # 作业对应的提交、未提交人数 [[提交数,未提交数],[提交数,未提交数]...]
        studentList = []
        for task in tasks:
            submitStudentDict = {}
            notSubmitStudentList = []

            # 属于这个作业的提交记录
            homeworkRecords = models.Homework.objects.filter(task=task)
            # 找出作业记录中的学生：查看谁已经提交了此次作业
            for homeworkRecord in homeworkRecords:
                if submitStudentDict.get(homeworkRecord.user.name, None) == None:
                    # {"唐" : UserProfile对象}
                    submitStudentDict[homeworkRecord.user.name] = homeworkRecord.user
            # 找出选了这个课的学生，再去掉已经提交作业的，剩下的就是没交作业的
            for selectedStudent in selectCourseStudentList:
                if submitStudentDict.get(selectedStudent.name, None) == None:
                    notSubmitStudentList.append(selectedStudent)
            submitStudentList = [submitStudent for submitStudent in submitStudentDict.values()]
            studentList.append([submitStudentList, notSubmitStudentList])

        tasks = list(zip(tasks, studentList))

        # tasks -->  [(task1, studentList1), (task2, studentList2), ...]
        # studentList --> [[提交用户列表,未提交用户列表],[提交用户列表,未提交用户列表]...]
        return render(request, 'teacherTasks.html', {'tasks': tasks, 'courseMsg':[courseNumber, coursename], 'selectCourseStudentList':selectCourseStudentList})
    else:
        return HttpResponseRedirect('/login/')

# 学生端：根据用户登录的名字筛选出ta所选的课程，传到前端
def studentCourseList(request):
    if request.user.username:
        courses = models.Course.objects.filter(members__user=request.user)
        taskCountList = [models.Task.objects.filter(courseBelongTo=course).count() for course in courses if course.status == u'Y']

        courseList = [course for course in courses if course.status == u'Y']
        return render(request, 'studentCourseList.html', {'course': zip(courseList, taskCountList)})

    else:
        return HttpResponseRedirect('/login/')

# 老师端：课程界面
def teacherCourseList(request):
    # 根据用户登录的名字筛选出ta所选的课程，传到前端
    if request.user.username:
        courses = models.Course.objects.filter(members__user=request.user)
        taskCountList = [models.Task.objects.filter(courseBelongTo=course).count() for course in courses if course.status == u'Y']

        isManager = True if request.user.is_superuser else False

        courseList = [course for course in courses if course.status == u'Y']
        return render(request, 'teacherCourseList.html', {'course': zip(courseList, taskCountList), 'isManager':isManager})

    else:
        return HttpResponseRedirect('/login/')

# 学生端上传作业
def post_file(request):
    if request.FILES.get('file', '') != '':
        file_obj = request.FILES.get('file')
        suffix = file_obj.name.split('.')[-1]
        task_id = request.POST.get('taskId')
        file_dir = os.path.join(BASE_DIR, 'file')
        task = models.Task.objects.get(id=task_id)
        title = task.title.replace('、', '_')
        task_dir = os.path.join(file_dir, task.courseBelongTo.courseNumber+task.courseBelongTo.courseName)
        task_dir = os.path.join(task_dir, title)
        if not os.path.exists(task_dir):
            os.makedirs(task_dir)
        file_name = title + '_' + request.user.profile.name + '_' + request.user.username + '.' + suffix
        file_path = os.path.join(task_dir, file_name)
        if not models.Homework.objects.filter(user = request.user.profile, task = task):
            models.Homework.objects.create(user=request.user.profile, task=task, filePath=file_path)
        else:
            tempHomeworkRecord = models.Homework.objects.filter(user=request.user.profile, task=task).first()
            tempHomeworkRecord.filePath = file_path
            tempHomeworkRecord.save()
        with open(file_path, 'wb') as f:
            f.write(file_obj.read())
        return HttpResponse('YES')

# 学生端下载作业
def download_file(request):
    if request.GET.get('url', '') != '':
        filename = request.GET["url"]
        task_title = filename.split('_')[0].replace('、', '_')
        filename = filename.replace('、', '_')
        course = models.Task.objects.filter(title=task_title)[0].courseBelongTo
        file = os.path.join(BASE_DIR, 'file', course.courseNumber+course.courseName, task_title, filename)

        def file_iterator(file_name, chunk_size=512):
            with open(file_name, 'rb') as f:
                while True:
                    c = f.read(chunk_size)
                    if c:
                        yield c
                    else:
                        break

        response = StreamingHttpResponse(file_iterator(file))
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = 'attachment;filename=' + filename.encode('utf-8').decode('ISO-8859-1')
        return response
    return HttpResponse('error')

# 老师下载作业
def teacherDownloadByHomeworknameAndStudentnumber(request):
    if request.method == 'POST':
        # json字符串
        studentNumber_taskName_JSON = request.body.decode("utf-8")
        # 转换为字典
        studentNumber_taskName_JSON = json.loads(studentNumber_taskName_JSON)
        # print(studentNumber_taskName_JSON["studentNumberList"])
        downloadTask = models.Task.objects.filter(title=studentNumber_taskName_JSON["taskName"]).first()
        filepathList = []
        for studentNumber in studentNumber_taskName_JSON["studentNumberList"]:
            filepathList.append(models.Homework.objects.filter(task=downloadTask, user__user__username=studentNumber).last().filePath)
        # 把文件转换成输出流
        def file_iterator(file_name, chunk_size=512):
            with open(file_name, 'rb') as f:
                while True:
                    c = f.read(chunk_size)
                    if c:
                        yield c
                    else:
                        break
        # 只有一个文件时直接传输
        if len(filepathList) == 1:
            fileName = filepathList[0].split('\\')[-1]
            print("正在传输：" + fileName)
            response = StreamingHttpResponse(file_iterator(filepathList[0]))
            response['Content-Type'] = 'application/octet-stream'
            response['Content-Disposition'] = 'attachment;filename=' + fileName.encode('utf-8').decode('ISO-8859-1')
            return response
        # 多个文件时打包成zip文件
        if len(filepathList) > 1:
            # 打包
            tempFile = zipfile.ZipFile("./file/temp/temp.zip", mode="w", compression=zipfile.ZIP_STORED, allowZip64=False)
            if not os.path.exists("./file/temp/"):
                os.makedirs("./file/temp/")
            for filepath in filepathList:
                tempFile.write(filepath, filepath.split("\\")[-1])
            tempFile.close()
            fileName = studentNumber_taskName_JSON["taskName"] + ".zip"
            response = StreamingHttpResponse(file_iterator("./file/temp/temp.zip"))
            response['Content-Type'] = 'application/octet-stream'
            response['Content-Disposition'] = 'attachment;filename=' + fileName.encode('utf-8').decode('ISO-8859-1')
            return response

        # response = StreamingHttpResponse(file_iterator())
        # response['Content-Type'] = 'application/octet-stream'
        # response['Content-Disposition'] = 'attachment;filename=' + filename.encode('utf-8').decode('ISO-8859-1')
        return HttpResponse("文件下载失败")

    else:
        return HttpResponse("文件下载失败")

# 老师添加作业/任务
def addHomework(request):
    if request.user.profile.type != 'T':
        return HttpResponse("您不是老师，无法添加！")
    if request.method != 'POST':
        return HttpResponse("请求方式错误！请重试！")

    homewordTitle = request.POST.get('title', "")
    homewordContent = request.POST.get('content', "请完成" + homewordTitle)
    uploadFileType = request.POST.get('uploadFileType', "*").replace('，', ',').replace('。','.').replace(';',',')
    courseNumber = request.POST.get('courseNumber', "")
    courseName = request.POST.get('courseName', "")
    if courseName == "" or courseNumber == "":
        return HttpResponse("任务失败")

    if homewordTitle == "":
        return HttpResponse("作业标题不能为空")
    if models.Task.objects.filter(title=homewordTitle).count() != 0:
        return HttpResponse("作业标题已经存在")

    course = models.Course.objects.filter(courseNumber=courseNumber, courseName=courseName).first()
    models.Task.objects.create(title=homewordTitle, content=homewordContent, uploadFileType=uploadFileType, courseBelongTo=course)

    return HttpResponseRedirect(request.headers.get("Referer"))

# 老师用户添加课程
def addCourse(request):
    if request.user.profile.type != 'T':
        return HttpResponse("您不是老师，无法添加！")
    if request.method != 'POST':
        return HttpResponse("请求方式错误！请重试！")

    courseName = request.POST.get('courseName', "")
    courseNumber = request.POST.get('courseNumber', "")
    studentList = request.POST.get('studentList', "")
    print("课程名：" + courseName + "课程编号：" + courseNumber)
    print("学生名单" + studentList)

    if courseName == "" or courseNumber == "" or studentList == "":
        return HttpResponse("课程信息有错误，请重新填写")
    if models.Course.objects.filter(courseName=courseName, courseNumber=courseNumber).count() != 0:
        return HttpResponse("该课程已经存在！无法添加")
    studentList = [student for student in studentList.split(';')]
    if studentList[-1] == "":
        studentList = studentList[0:-1]

    #创建不存在的学生
    for studentStr in studentList:
        if models.User.objects.filter(username=studentStr.split(',')[0]).count() == 0:
            models.User.objects.create_user(username=studentStr.split(',')[0], password="szu" + studentStr.split(',')[0][4:])
            models.UserProfile.objects.create(name=studentStr.split(',')[1], user=models.User.objects.filter(username=studentStr.split(',')[0]).first(), type='S', gender='M' if studentStr.split(',')[2] == '男' else 'F')
    #创建课程
    models.Course.objects.create(courseName=courseName, courseNumber=courseNumber)
    # 获得刚创建的课程
    course = models.Course.objects.filter(courseName=courseName, courseNumber=courseNumber).first()
    # 添加学生
    for studentStr in studentList:
        course.members.add(models.UserProfile.objects.filter(user__username=studentStr.split(',')[0]).first())
    # 添加老师
    course.members.add(models.UserProfile.objects.filter(user=request.user).first())

    return HttpResponseRedirect(request.headers.get("Referer"))

# 进入管理员界面
def manager(request):
    if not request.user.is_superuser:
        HttpResponse("警告！您不是管理员！无法进入此界面！")

    teacher = models.UserProfile.objects.filter(type='T')
    student = models.UserProfile.objects.filter(type='S')

    return render(request, 'manager.html', {'teacherList':teacher, 'studentList':student})

# 管理员添加成员
def addMemberByManager(request):
    if not request.user.is_superuser:
        return HttpResponse("您不是管理员，无法添加！")
    if request.method != 'POST':
        return HttpResponse("请求方式错误！请重试！")

    memberType = request.POST.get('memberType', '')
    memberName = request.POST.get('memberName', '')
    memberNumber = request.POST.get('memberNumber', '')
    memberGender = request.POST.get('memberGender', '')
    memberPassword = request.POST.get('memberPassword', '') if memberType == 'teacher' else "szu" + memberNumber[4:]
    print(memberPassword)
    if memberType == "" or memberName == "" or memberNumber == "" or memberGender == "" or memberPassword == "":
        return HttpResponse("成员信息缺失！请重新添加！")
    if models.User.objects.filter(username=memberNumber).count() != 0:
        return HttpResponse("该成员已存在！无法添加！")

    models.User.objects.create_user(username=memberNumber, password=memberPassword)
    member = models.User.objects.filter(username=memberNumber).first()
    models.UserProfile.objects.create(name=memberName, type='T' if memberType == 'teacher' else 'S', gender='M' if memberGender == 'male' else 'F', user=member)

    return HttpResponseRedirect(request.headers.get("Referer"))

# 管理员删除用户
def deleteMemberByManager(request, memberNumber):
    if not request.user.is_superuser:
        return HttpResponse("您不是管理员，无法删除！")
    print("正在删除用户：" + memberNumber)
    if models.User.objects.filter(username=memberNumber).count() == 0 or models.UserProfile.objects.filter(user__username=memberNumber).count() == 0:
        return HttpResponse("该用户不存在，无法删除")
    if models.User.objects.filter(username=memberNumber).first().is_superuser:
        return HttpResponse("无法删除管理员！")

    models.User.objects.filter(username=memberNumber).delete()

    return HttpResponseRedirect(request.headers.get('Referer'))

# 老师端：更新课程信息
def changeCourseMsgByTeacher(request):
    if request.user.profile.type != 'T':
        return HttpResponse("您不是老师，无法修改课程信息！")
    if request.method != 'POST':
        return HttpResponse("请求方式错误！请重试！")

    if request.POST.get("changedCourseName", None) == None or request.POST.get("changedCourseName", None) == None:
        return HttpResponseRedirect(request.headers.get('Referer'))

    courseNumber = request.POST.get("courseNumber")
    courseName = request.POST.get("courseName")
    changedCourseName = request.POST.get("changedCourseName")
    changedCourseNumber = request.POST.get("changedCourseNumber")

    if models.Course.objects.filter(courseNumber=courseNumber, courseName=courseName).count() == 0:
        return HttpResponse("该课程不存在！请重试！")
    course = models.Course.objects.filter(courseNumber=courseNumber, courseName=courseName).first()
    course.courseName = changedCourseName
    course.courseNumber = changedCourseNumber
    course.save()

    return HttpResponseRedirect('/teacherCourseList/')

# 老师端：删除作业/任务
def deleteTaskByTeacher(request, taskId):
    if request.user.profile.type != 'T':
        return HttpResponse("您不是老师，无法删除该作业！")
    if models.Task.objects.filter(id = taskId).count() == 0:
        return HttpResponse("该作业不存在！无法删除该作业！")
    task = models.Task.objects.filter(id = taskId).first()
    for homework in models.Homework.objects.filter(task=task):
        homework.delete()
    task.delete()
    return HttpResponseRedirect(request.headers.get('Referer'))

# 老师端：从课程中移除学生
def removeStudentFromCourse(request, studentNumber, courseNumber, courseName):
    if request.user.profile.type != 'T':
        return HttpResponse("您不是老师，无法进行该操作！")
    if models.Course.objects.filter(courseNumber=courseNumber, courseName=courseName).count() == 0 or models.User.objects.filter(username=studentNumber).count() == 0:
        return HttpResponse("此课程或此学生不存在！")
    course = models.Course.objects.filter(courseNumber=courseNumber, courseName=courseName).first()
    student = models.UserProfile.objects.filter(user__username=studentNumber).first()
    course.members.remove(student)

    return HttpResponseRedirect(request.headers.get('Referer'))

def addStudentToCourseByTeacher(request):
    if request.user.profile.type != 'T':
        return HttpResponse("您不是老师，无法修改课程信息！")
    if request.method != 'POST':
        return HttpResponse("请求方式错误！请重试！")

    studentName = request.POST.get("newStudentName", "")
    studentNumber = request.POST.get("newStudentNumber", "")
    studentGender = request.POST.get("newStudentGender", "")
    courseNumber = request.POST.get("courseNumber", "")
    courseName = request.POST.get("courseName", "")
    if studentName == "" or studentNumber == "" or studentGender == "" or courseNumber == "" or courseName == "":
        return HttpResponse("填入的参数有误，请重试！")
    if models.Course.objects.filter(courseNumber=courseNumber, courseName=courseName).count() == 0:
        return HttpResponse("该课程不存在，请重试")
    course = models.Course.objects.filter(courseNumber=courseNumber, courseName=courseName).first()
    if models.UserProfile.objects.filter(user__username=studentNumber).count() != 0:
        student = models.UserProfile.objects.filter(user__username=studentNumber).first()
    else:
        user = models.User.objects.create_user(username=studentNumber, password="szu" + studentNumber[4:])
        student = models.UserProfile.objects.create(user=user, name=studentName, gender=studentGender, type='S')
    course.members.add(student)
    return HttpResponseRedirect(request.headers.get('Referer'))


def create_student_user():
    users = load_user_list()
    for user in users:
        user_obj = User.objects.create_user(username=user[0], password='szu'+user[0][-6:])
        if user[2] == '男':
            sex = u'M'
        else:
            sex = u'F'
        models.UserProfile.objects.create(name=user[1], gender=sex, user_id=user_obj.id)
