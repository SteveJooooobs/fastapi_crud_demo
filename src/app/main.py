# FastAPI 应用入口
from fastapi import FastAPI

# 导入数据库引擎和基类
from app.db.session import engine
from app.db.base import Base

# 导入所有模型（必须导入，否则 Base 不知道有哪些表需要创建）
from app.models import Category, Knowledge

app = FastAPI(
    title = "知识库 API",
    description = "FastAPI + SQLAlchemy 知识库增删改查练手项目",
    version = "0.1.0"
)

# ========== 创建数据库表 ==========
# 遍历所有继承 Base 的模型，在数据库中创建对应的表
# 如果表已存在，则跳过（不会覆盖或删除现有数据）
Base.metadata.create_all(bind=engine)

@app.get("/")
async def root():
    """测试服务是否正常运行"""
    return {"message": "知识库 API 服务运行中", "status": "ok"}


@app.get("/health")
async def check_health():
    """健康检查接口，留空后续补充"""
    return {"status": "healthy"}