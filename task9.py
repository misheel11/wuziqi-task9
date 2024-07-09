import requests as req
import re
import time as t
import copy


# 棋形匹配
l = [[] for i in range(5)]
l[4] = ["11111"]
l[3] = ["011110", "211110"]
l[2] = ["11101",  "20222", "22022", "22202", "22220", "022020", "02220", "01110", "211100", "2011102"]
l[1] = ["011010", "11011", "211010", "210110", "11001", "001100", "211000"]
l[0] = ["10101", "01010", "010010", "210100", "210010", "10001"]

opponent_first = 1
myai_first = 0  # 设置先后手
first = opponent_first  # 默认先手为对手， 即对手持黑，后续判断里会进行修改，此处仅为了声明一个全局变量,也可用none定义

b_num = 0  # 黑子个数
w_num = 0  # 白子个数

MAX = 10000000000  # 正无穷
MIN = -10000000000  # 负无穷
deep = 3  # 规定ai搜索深度

chess = [[0] * 15 for i in range(15)]  # 用来判断棋盘某处是否有棋,1为黑棋, -1为白棋, 0为空

point = [[-1] * 3 for i in range(200)]  # 存储n中走法对应的点的横坐标[n][0]纵坐标[n][1]及value值[n][2]
num_points = 0  # 记录可走步的个数
p1 = [0, 0]  #
p2 = [0, 0]  #


# 棋形与分值索引
values = {
    # 连五
    "11111": 999900000,
    # 活四
    "011110": 33300000,
    # 冲四
    "211110": 6250000,
    "11101": 6250000,
    "11011": 6250000,
    # 御敌
    "02220": 525000,
    "20222": 725000,
    "22022": 725000,
    "22202": 725000,
    "22220": 725000,
    "022020": 725000,
    # 活三
    "01110": 625000,
    "011010": 625000,
    # 眠三
    "211100": 12500,
    "211010": 12500,
    "210110": 12500,
    "11001": 12500,
    "10101": 12500,
    "2011102": 12500,
    # 活二
    "001100": 250,
    "01010": 250,
    "010010": 250,
    # 眠二
    "211000": 25,
    "210100": 25,
    "210010": 25,
    "10001": 25,
    # 其他
    "others": 8
}

# 位置得分， 越靠近中心位置分越高
values_of_pos = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0],
    [0, 2, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 2, 0],
    [0, 2, 4, 6, 6, 6, 6, 6, 6, 6, 6, 6, 4, 2, 0],
    [0, 2, 4, 6, 7, 7, 7, 7, 7, 7, 7, 6, 4, 2, 0],
    [0, 2, 4, 6, 7, 8, 8, 8, 8, 8, 7, 6, 4, 2, 0],
    [0, 2, 4, 6, 7, 8, 9, 9, 9, 8, 7, 6, 4, 2, 0],
    [0, 2, 4, 6, 7, 8, 9, 10, 9, 8, 7, 6, 4, 2, 0],
    [0, 2, 4, 6, 7, 8, 9, 9, 9, 8, 7, 6, 4, 2, 0],
    [0, 2, 4, 6, 7, 8, 8, 8, 8, 8, 7, 6, 4, 2, 0],
    [0, 2, 4, 6, 7, 7, 7, 7, 7, 7, 7, 6, 4, 2, 0],
    [0, 2, 4, 6, 6, 6, 6, 6, 6, 6, 6, 6, 4, 2, 0],
    [0, 2, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 2, 0],
    [0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]


# 更新先后手状态
def renew_first(Order):
    global first
    if (len(Order) // 2) % 2 == 0:  # 我是黑方，我先手
        first = myai_first
    else:  # 我是白方，我后手，对手先手
        first = opponent_first


# 更新chess状态
def renew_chess(Order):
    global chess, b_num, w_num
    for xx in range(15):
        for yy in range(15):
            chess[xx][yy] = 0

    step = 0  # 步数 用于判断黑白 黑方先走
    renew_first(Order)

    for i in range(0, len(Order), 4):  # i = 0 4 8 12 16
        chess[ord(Order[i]) - 97][ord(Order[i + 1]) - 97] = 1
        b_num += 1
    for i in range(2, len(Order), 4):  # i = 2 6 10 14 18
        chess[ord(Order[i]) - 97][ord(Order[i + 1]) - 97] = -1
        w_num += 1

    for xx in range(15):
        for yy in range(15):
            print(chess[xx][yy])
        print('\n')


# 获取以p点为中心的9个点的连线棋形  dir_offset:方向偏移
def getline(chess, px, py, dir_offset, opponent_color):
    line = [0 for i in range(9)]
    tmp_x = px + (-5 * dir_offset[0])
    tmp_y = py + (-5 * dir_offset[1])
    for i in range(9):
        tmp_x += dir_offset[0]
        tmp_y += dir_offset[1]
        if tmp_x < 0 or tmp_x >= 15 or tmp_y < 0 or tmp_y >= 15:
            line[i] = opponent_color  # 若超界则假设为对手棋
        else:
            line[i] = chess[tmp_y][tmp_x]  # 黑1白-1
    return line


# 分析棋形并得到该方向的分值,最后的参数是,有利分为1不利分为-1
def get_line_score(line, ai_color, opponent_color, weight, px, py):
    global l, values
    new_line = list(range(9))
    num = 0  # 统计连子个数
    for i in range(line.index(ai_color), 9):
        if line[i] == ai_color:
            num += 1
    # 将line格式统一化,转字符串,己方棋子为1，对方棋子为2，空为0，便于匹配
    for i in range(9):
        if line[i] == ai_color:
            new_line[i] = '1'
        elif line[i] == opponent_color:
            new_line[i] = '2'
        else:
            new_line[i] = '0'
    s = ''.join(new_line)  # 转化为字符串
    fan_s = s[::-1]  # 字符串反转
    # 逐个匹配
    if num > 5:
        return values["11111"] * weight
    if 5 >= num >= 1:
        for each in l[num - 1]:
            result = re.search(each, s)
            if result is not None:  # 找到匹配项
                return (values[result.group()] + values_of_pos[py][px]) * weight
            result = re.search(each, fan_s)
            if result is not None:  # 找到匹配项
                return (values[result.group()] + values_of_pos[py][px]) * weight
    # 未找到匹配项，为单子情况
    return (values["others"] + values_of_pos[py][px]) * weight


# 评估函数，评估当前棋局的分值
def Evaluate(chess):
    advantage = 0  # 有利分, 对上一层有利的分！！
    disadvantage = 0  # 不利分, 对方AI所持棋子得分, 取负
    ai_color = 0  # ai所持棋子颜色
    opponent_color = 0  # 对手所持棋子颜色
    dir_offset = [(1, 0), (0, 1), (1, 1), (1, -1)]  # 四个方向，右，上，右上，右下
    if first == opponent_first:
        ai_color = 1  # 己方ai持白子
        opponent_color = -1
    if first == myai_first:
        ai_color = -1  # 己方ai持黑子
        opponent_color = 1
    for k in range(4):
        line = getline(chess, p2[0], p2[1], dir_offset[k], opponent_color)  # 获得此方向的连线棋形
        advantage += get_line_score(line, ai_color, opponent_color, 1, p2[0], p2[1])  # 分析棋形并得到该方向的分值 有利得分, 权重小于1以增强攻击性
        line = getline(chess, p1[0], p1[1], dir_offset[k], ai_color)  # 获得此方向的连线棋形
        disadvantage += get_line_score(line, opponent_color, ai_color, -1, p1[0], p1[1])  # 分析棋形并得到该方向的分值 不利得分
    return advantage + disadvantage


# 获取下一步所有可能走法的点位
def get_next_pos(tchess, b_num):
    num_pos = 0
    positions = [[-1] * 2 for i in range(200)]
    top = 0
    borrow = 0
    left = 0
    right = 0
    find = False
    for i in range(15):
        if find:
            break
        for j in range(15):
            if tchess[i][j] != 0:  # 该处有棋
                top = i  # 此棋局棋子落下的范围-上
                find = True
                break
    find = False
    for i in range(15):
        if find:
            break
        for j in range(15):
            if tchess[14 - i][j] != 0:  # 该处有棋
                borrow = 14 - i  # 此棋局棋子落下的范围-下
                find = True
                break
    find = False
    for i in range(15):
        if find:
            break
        for j in range(15):
            if tchess[j][i] != 0:  # 该处有棋
                left = i  # 此棋局棋子落下的范围-左
                find = True
                break
    find = False
    for i in range(15):
        if find:
            break
        for j in range(15):
            if tchess[j][14 - i] != 0:  # 该处有棋
                right = 14 - i  # 此棋局棋子落下的范围-右
                find = True
                break
    if b_num <= 10:
        scope = 1
    else:
        scope = 1
    if top - scope >= 0:  # 假设下一步走的棋的位置不超过当前棋局范围四格， 缩小范围，提高效率
        top -= scope
    else:
        top = 0
    if borrow + scope < 15:
        borrow += scope
    else:
        borrow = 14
    if left - scope >= 0:
        left -= scope
    else:
        left = 0
    if right + scope < 15:
        right += scope
    else:
        right = 14
    for i in range(top, borrow + 1):
        for j in range(left, right + 1):
            if tchess[i][j] == 0:  # 该处可以走步
                positions[num_pos][0] = j
                positions[num_pos][1] = i  # 记下可走步的x,y
                num_pos += 1
    return positions, num_pos


# 将p点放入棋盘布局
def set_newchess(new_chess, p, max_or_min):
    # max(1), min(-1), 黑棋(1), 白棋(-1), me_first(1), ai_first(0)
    if first == opponent_first:
        new_chess[p[1]][p[0]] = max_or_min
    if first == myai_first:
        new_chess[p[1]][p[0]] = -1 * max_or_min


# 获取棋子在某个方向上连续的最大个数,最后的参数是棋子颜色对应的标记
def one_dir_num(x, y, dx, dy, chess, b_or_w):
    xi = int(x)
    yi = int(y)
    sum = 0
    while True:
        xi += dx
        yi += dy
        if xi < 0 or xi >= 15 or yi < 0 or yi >= 15 or chess[yi][xi] != b_or_w:
            return sum
        sum += 1


def check_win_in_alpha_beta(chess):
    # 四个方向数组
    director = [[(-1, 0), (1, 0)], [(0, -1), (0, 1)], [(-1, -1), (1, 1)], [(-1, 1), (1, -1)]]
    if first == opponent_first:
        color = -1
    if first == myai_first:
        color = 1
    # 检查ai所持棋子
    # 遍历每一个该色棋子
    for i in range(15):
        for j in range(15):
            if chess[i][j] != color:
                continue
            for d1, d2 in director:
                dx, dy = d1
                num1 = one_dir_num(int(j), int(i), dx, dy, chess, color)
                dx, dy = d2
                num2 = one_dir_num(int(j), int(i), dx, dy, chess, color)
                if num1 + num2 >= 5:
                    return MIN  # 赢
    return -1


# alpha-beta剪枝搜索，返回最好的值
def alpha_beta(depth, max_or_min, chess, alpha, beta):
    global point, num_points, i
    if depth == 1:  # 最后一层
        return Evaluate(chess)  # 评估函数，评估当前棋局的分值,pp为此棋局的最后一个子的位置
    positions, num_pos = get_next_pos(chess, b_num)  # 获取下一步所有可能走法的点位
    if depth == deep:
        num_points = num_pos
        for i in range(num_points):
            point[i][0], point[i][1] = positions[i][0], positions[i][1]  # 保存可能走到的位置的x,y
    if max_or_min == 1:  # MAX层
        # 对于每一个可能的走步
        for p in range(num_pos):
            new_chess = copy.deepcopy(chess)  # 拷贝旧棋局
            set_newchess(new_chess, positions[p], max_or_min)  # 将此步放置到新棋局上
            p2[0], p2[1] = positions[p][0], positions[p][1]
            score = alpha_beta(depth - 1, -1 * max_or_min, new_chess, alpha, beta)  # 得到它的下一层的值score
            if depth == deep:
                point[p][2] = score
            if score > alpha:
                alpha = score
            if alpha >= beta:
                return alpha  # 此处为aplha-beta剪枝
        return alpha
    if max_or_min == -1:  # MIN层
        for p in range(num_pos):  # 对于每一个可能的走步
            new_chess = copy.deepcopy(chess)  # 拷贝旧棋局
            set_newchess(new_chess, positions[p], max_or_min)  # 将此步放置到新棋局上
            p1[0], p1[1] = positions[p][0], positions[p][1]
            win = check_win_in_alpha_beta(new_chess)  # 检查此步是否为绝杀，若为绝杀直接返回
            if win == MIN:
                beta = MIN
                point[i][2] = MIN
                return beta
            score = alpha_beta(depth - 1, -1 * max_or_min, new_chess, alpha, beta)  # 得到它的下一层的值score
            if depth == deep:
                point[p][2] = score
            if score < beta:
                beta = score
            if beta <= alpha:
                return beta  # 此处为aplha-beta剪枝
        return beta


# 获取对应value值的走法的位置
def get_point(value):
    global point, num_points
    pp = [[-1] * 3 for i in range(num_points)]  # 存储找到的值为value的点的坐标
    np = 0
    for i in range(num_points):
        if point[i][2] == value:
            return int(point[i][0]), int(point[i][1])


# 棋子确定
def ensure_loc():
    global b_num, w_num, point, num_points, p1, p2
    p1 = [0, 0]
    p2 = [0, 0]
    if first == myai_first and b_num == 0:
        xq = 7
        yq = 7
    else:
        max_or_min = -1
        point = [[-1] * 3 for i in range(200)]  # 存储n中走法对应的点的横坐标[n][0]纵坐标[n][1]及value值[n][2]
        num_points = 0  # 记录可走步的个数
        # 利用极大极小值搜索和alpha-beta剪枝获取最小value值
        value = alpha_beta(deep, max_or_min, chess, MIN, MAX)  # alpha初始为负无穷，beta初始为正无穷
        # 得到value对应的走法位置（若有多个则随机选择一个）
        xq, yq = get_point(value)  # 获取value值对应的走法位置
    return chr(yq + 97) + chr(xq + 97)


def fastModular(x):
    """x[0] = base """
    """x[1] = power"""
    """x[2] = modulus"""
    result = 1
    while x[1] > 0:
        if x[1] & 1:
            result = result * x[0] % x[2]
        x[1] = int(x[1] / 2)
        x[0] = x[0] * x[0] % x[2]
    return result


def str_to_num(strings):
    sum = 0
    lens = len(strings)
    for i in range(0, lens):
        sum += ord(strings[i]) * 256 ** (lens - i - 1)
    return sum


def encodeLogin(password):
    # 公钥
    power = 65537
    modulus = 135261828916791946705313569652794581721330948863485438876915508683244111694485850733278569559191167660149469895899348939039437830613284874764820878002628686548956779897196112828969255650312573935871059275664474562666268163936821302832645284397530568872432109324825205567091066297960733513602409443790146687029

    return hex(fastModular([str_to_num(password), power, modulus]))


def join_game(user, myHexPass):
    """加入游戏并返回一个 get回复包对象"""

    url = 'http://183.175.12.27:8001/join_game/'
    param = {
        'user': user,
        'password': myHexPass,
        'data_type': 'json'
    }

    getHtml = req.get(url, params=param)

    print("Open a new game{getHtml.text}")
    return getHtml


def check_game(game_id):
    url = 'http://183.175.12.27:8001/check_game/' + str(game_id)
    getState = req.get(url)
    # print(getState.text)    # 测试显示数据用
    return getState


def play_game(user, myHexPass, game_id, coord):
    url = 'http://183.175.12.27:8001/play_game/' + str(game_id)
    param = {
        'user': user,
        'password': myHexPass,
        'data_type': 'json',
        'coord': coord
    }
    req.get(url, params=param)


user = '0191595031'
password = '12344321'
myHexPass = encodeLogin(password)

game_id = join_game(user, myHexPass).json()["game_id"]
state = check_game(game_id).json()

print("Looking forgame partners ...")
while state['ready'] == "False":
    state = check_game(game_id).json()
    print(state['ready'], end=" ")
    t.sleep(5)

if state['creator'] != user:
    opponent = state['creator']
else:
    opponent = state['opponent_name']

while state['ready'] == "True":
    if state['current_turn'] == user:
        order = state['board']
        renew_chess(order)
        coord = ensure_loc()
        play_game(user, myHexPass, game_id, coord)
        print("Playing {coord}")
    else:
        print("Waiting for {opponent} to play")

    t.sleep(5)
    state = check_game(game_id).json()

    if state['winner'] != "None":
        print("The winner is {state['winner']}")
        break
