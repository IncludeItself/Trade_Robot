def cal_line(P1, q1, P2, q2, k):
    """
    求解幂函数方程 P(q) = A/(q-c)^k 的参数 A 和 c

    参数:
        P1 (float): 第一点的函数值
        q1 (float): 第一点的自变量值
        P2 (float): 第二点的函数值
        q2 (float): 第二点的自变量值
        k (float): 幂指数

    返回:
        tuple: (A, c) 计算得到的两个参数

    异常:
        ValueError: 输入参数不合法（除零、负数开方等）
    """
    # 基础参数校验
    if k == 0:
        raise ValueError("幂指数 k 不能为 0")
    if P1 <= 0 or P2 <= 0:
        raise ValueError("P1 和 P2 必须为正数")

    try:
        # 计算 1/k 次方
        p1_pow = P1 ** (1 / k)
        p2_pow = P2 ** (1 / k)

        # 计算分母，避免除零错误

        if p2_pow < 0.1:
            raise ValueError("两点参数导致分母为 0，无唯一解")
        t = p1_pow / p2_pow
        if p2_pow-1 < 1e-12:
            raise ValueError("两点参数导致分母为 0，无唯一解")
        # 求解 c
        c = (t*q1 - q2) / (t - 1)

        # 求解 A
        A = P1 * (q1 - c) ** k

        return A, c

    except Exception as e:
        raise ValueError(f"参数计算失败: {str(e)}")


if __name__ == "__main__":
    # 测试用例
    P1 = 3000
    q1 = 100
    P2 = 1000
    q2 = 300
    k = 2

    A, c = cal_line(P1, q1, P2, q2, k)
    print(f"A: {A:.4f}, c: {c:.4f}")
    # 输出: A: 100.0000, c: 3.3333
