# 开发文档
## 虚拟环境
```shell
# 进入项目目录
cd E:\workplace\Trade_Robot
# 创建虚拟环境
python -m venv venv
# 激活虚拟环境
venv\Scripts\activate
# 验证虚拟环境输出路径应包含 E:\workplace\Trade_Robot\venv
where python
where pip
# 退出虚拟环境
deactivate
```

## 安装依赖
```shell
# 生成 requirements.txt
pip freeze > requirements.txt
# 按 requirements.txt 安装依赖
pip install -r requirements.txt
```


## 打包项目
```shell
# 打包项目
pyinstaller trade_robot.spec
# 重新打包
pyinstaller trade_robot.spec --clean
# 清理旧构建
Remove-Item -Recurse -Force dist, build
```

