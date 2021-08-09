# 拟定将导航路线存储到数据库, 客户端向服务请求路径信息
# 远程控制端控制指令包含(速度, 路径ID, 等关键信息) 车端收到控制指令后再次向服务器请求路径数据

def gen_trajectory(_id=0, _name="path1"):
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


# 获取组内可用路径(查数据库)
def getAvailbalePaths(group):
    return [{'id': 0, 'name': "路径0"}, {'id': 1, 'name': "路径1"}]


# 获取路径数据(查数据库)
def getNavPath(path_id):
    print(path_id)
    if path_id == 0:
        path = gen_trajectory(0, "路径0")
    elif path_id == 1:
        path = gen_trajectory(1, "路径1")
    else:
        return None
    print(path_id, path)
    return path
