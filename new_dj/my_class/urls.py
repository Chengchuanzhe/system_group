"""my_class URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,re_path
from app01 import views

from django.views import static ##新增
from django.conf import settings ##新增


urlpatterns = [
    # 用户loading
    path('admin/', admin.site.urls),
    path('login/', views.log_in),
    path('logout/',views.log_out,name='logout'),
    path('user/', views.user),
    # 学生端操作
    path('studentTasks/<str:courseNumber>/<str:coursename>/', views.studentGetTaskByCoursename, name='studentGetTask'),
    path('studentCourseList/', views.studentCourseList, name='studentCourseList'),
    path('upload_file', views.post_file, name='upload_file'),
    path('download-file',views.download_file,name='download_file'),
    #管理员操作
    path('manager/', views.manager, name='manager'),
    path('addMemberByManager/', views.addMemberByManager, name='addMemberByManager'),
    path('deleteMemberByManager/<str:memberNumber>/', views.deleteMemberByManager, name='deleteMemberByManager'),
    # 老师端操作
    path('teacherCourseList/', views.teacherCourseList, name='teacherCourseList'),
    path('teacherTasks/<str:courseNumber>/<str:coursename>/', views.teacherGetTaskByCoursename, name='teacherGetTask'),
    path('download_homework_ByTeacher/',views.teacherDownloadByHomeworknameAndStudentnumber, name='download_homework_ByTeacher'),
    path('addHomework/',views.addHomework, name='addHomework'),
    path('addCourse/', views.addCourse, name='addCourse'),
    path('changeCourseMsgByTeacher/', views.changeCourseMsgByTeacher, name='changeCourseMsgByTeacher'),
    path('deleteTaskByTeacher/<str:taskId>/', views.deleteTaskByTeacher, name='deleteTaskByTeacher'),
    path('removeStudentFromCourse/<str:courseNumber>/<str:courseName>/<str:studentNumber>/', views.removeStudentFromCourse, name='removeStudentFromCourse'),
    path('addStudentToCourseByTeacher/', views.addStudentToCourseByTeacher, name='addStudentToCourseByTeacher'),

    #静态资源导入
    re_path(r'^static/(?P<path>.*)$', static.serve,
        {'document_root': settings.STATIC_ROOT}, name='static'),
]
