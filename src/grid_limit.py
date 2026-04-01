import logging

from src import state

def grid_allow(direction,symbol, price,pos_qty):

    test_logger = logging.getLogger("test_logger")
    logger = logging.getLogger("grid_allow")
    test_logger.info(f"grid allow: {direction}  {symbol} 当前价格：{price}，当前持仓数量：{pos_qty}")
    grid=state.t_grid.get(symbol,{})
    test_logger.info(f"grid in grid_allow:{grid}")
    if grid:
        grid.sort(key=lambda x: x["price"],reverse=True)
        index=0
        while index<len(grid)-1:
            if grid[index]["price"]>price:
                index += 1
                continue
            else:
                break
        test_logger.info(f"grid allow: {direction}  {symbol} 当前价格：{price}，当前持仓数量：{pos_qty}，当前网格价格：{grid[index]["price"]}，当前网格数量：{grid[index]["qty"]}")
        logger.info(f"grid allow: {direction}  {symbol} 当前价格：{price}，当前持仓数量：{pos_qty}，当前网格价格：{grid[index]["price"]}，当前网格数量：{grid[index]["qty"]}")
        if direction=="Buy":
            if index>=len(grid):
                return 0
            return max(0,grid[index]["qty"]-pos_qty)
        else:
            if index<=0:
                return 0
            return max(0,pos_qty-grid[index-1]["qty"])

    return 0
