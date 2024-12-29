from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    # django自带用户，一对一关系
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    name = models.CharField('姓名', max_length=20, blank=False,default='未知')

    GENDER_CHOICES = (
        (u'M', u'男'),
        (u'F', u'女'),
    )
    gender = models.CharField('姓别', max_length=2, choices=GENDER_CHOICES, default='M')

    TYPE_CHOICES = (
        (u'T', u'老师'),
        (u'S', u'学生'),
    )
    type = models.CharField('类型', max_length=2, choices=TYPE_CHOICES, default='S')

    # type = models.
    class Meta:
        verbose_name = '教学用户'

    def __str__(self):
        return self.user.__str__()


class Course(models.Model):
    # 课程名
    courseName = models.CharField(max_length=30, null=False, unique=False, default='未命名课程')
    # 课程编号
    courseNumber = models.CharField(max_length=30, null=False, unique=False, default='000000')
    # 课程里的人员，包括老师和学生
    members = models.ManyToManyField(UserProfile)
    # 开设状态选择
    OPEN_CHOICES = (
        (u'Y', u'开启'),
        (u'N', u'关闭'),
    )
    # 开设状态
    status = models.CharField('开设状态', max_length=10, choices=OPEN_CHOICES, default=u'Y')

    class Meta:
        verbose_name = "课程"

    def __str__(self):
        return self.courseName + ": " + self.courseNumber



class Task(models.Model):
    # 作业的标题
    title = models.CharField(max_length=100,null=False,unique=True, default='未命名作业')
    # 作业正文
    content = models.TextField(default='请修改作业正文~')
    # 是否显示
    DIS_CHOICES = (
        (u'Y', u'on'),
        (u'N', u'off'),
    )
    display = models.CharField('显示', max_length=2, choices=DIS_CHOICES, default='Y')
    # 此次作业属于哪个课程
    courseBelongTo = models.ForeignKey(Course, on_delete=models.CASCADE)
    # 此次作业可以上传的文件类型
    uploadFileType = models.CharField(max_length=30, default='*')

    class Meta:
        verbose_name = "作业"

    def __str__(self):
        return self.title


# 一个提交记录就是一个数据
class Homework(models.Model):
    # 此次提交的用户是谁
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, default='')
    # 此次提交的作业是
    task = models.ForeignKey(Task, on_delete=models.CASCADE, default='')
    # 提交的时间
    time = models.DateTimeField(auto_now=True)
    # 文件的路径
    filePath = models.CharField(max_length=100, default='/file', null=False, unique=False)


    class Meta:
        verbose_name = "提交记录"




