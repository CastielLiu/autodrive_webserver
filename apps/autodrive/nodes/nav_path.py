# 拟定将导航路线存储到数据库, 客户端向服务请求路径信息
# 远程控制端控制指令包含(速度, 路径ID, 等关键信息) 车端收到控制指令后再次向服务器请求路径数据
from apps.autodrive.models import NavPathInfo
from django.db.models import Q, F

from apps.autodrive.utils import debug_print


def gen_test_trajectory(_id=0, _name="path1"):
    start_point = (33.3794, 120.16574722)
    end_point = (33.372647, 120.155741)

    size = 30
    dx = (end_point[0] - start_point[0]) / size
    dy = (end_point[1] - start_point[1]) / size

    path = []

    for i in range(size):
        point = {"lng": start_point[1] + dy * i, "lat": start_point[0] + dx * i}
        path.append(point)
    res = {'id': _id, 'name': _name, 'points': path}
    print("res", res)
    return res


def getTestNavPath(group_name, path_id):
    if path_id == 0:
        path = gen_test_trajectory(0, "路径0")
    elif path_id == 1:
        path = gen_test_trajectory(1, "路径1")
    else:
        return False, "Path not exist", None
    return True, "", path


# 获取组内可用路径(查数据库)
def getAvailbalePaths(group_id):
    paths = NavPathInfo.objects.filter(Q(uploader__group__id=group_id) & Q(is_active=True))
    path_list = [{'id': path.id, 'name': path.name} for path in paths]
    return path_list


# 获取路径轨迹数据(查数据库)
# @param group_id 获取组内路径
# @param path_id 路径ID
def getNavPathTraj(group_id, path_id):
    try:
        debug_print("getNavPathTraj path_id:%d, group_id:%s" % (path_id, group_id))
        navpaths = NavPathInfo.objects.filter(Q(id=path_id) & Q(uploader__group__id=group_id) & Q(is_active=True))
        if navpaths.count() == 0:
            return False, "Path not exist", None
        navpath = navpaths[0]
    except Exception as e:
        return False, "Qurey Path failed", None

    path_result = {'id': path_id, 'name': navpath.name, 'points': []}

    try:
        with open(navpath.points_file.path) as f:
            line = f.readline()
            titles = line.split()
            info_cnt = len(titles)
            if info_cnt < 2:
                return False, 'Invalid title count in path', None
            try:
                lat_index = titles.index('lat')
                lng_index = titles.index('lng')
            except Exception as e:
                return False, 'Invalid title in path: '+e.args[0], None

            while line:
                line = f.readline()
                infos = line.split()
                if len(infos) != info_cnt:
                    break
                path_result['points'].append({"lng": infos[lng_index], "lat": infos[lat_index]})
    except Exception as e:
        return False, 'Path file error', None

    if len(path_result['points']) == 0:
        return False, "No points in file", None
    return True, "", path_result


# 获取导航路径文件
def getNavPathFiles(group_name, path_id):
    navpaths = NavPathInfo.objects.filter(Q(id=path_id) & Q(uploader__group__name=group_name) & Q(is_active=True))
    if navpaths.count() == 0:
        return False, "Path not exist", None

    navpath = navpaths[0]










