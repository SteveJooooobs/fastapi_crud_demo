API接口和SQLAlchemy知识库项目的笔记

---

## 笔记内容

```markdown
# FastAPI + SQLAlchemy 知识库项目 - 学习笔记

## 项目概述
- 项目路径：`F:\PyPrc\FastApi_learn\fastapi_crud_demo`
- 技术栈：FastAPI + SQLAlchemy + Pydantic V2 + MySQL
- 功能：知识库的增删改查（Category 单级分类 + Knowledge 知识条目）

```

## 一、环境配置相关

### Q1：.env 文件是做什么的？里面填充的内容只有这些吗？
**A：** `.env` 文件用于本地存储敏感配置（如数据库密码、API 密钥），会被 `.gitignore` 忽略，不会上传到 GitHub。配置项包括：

- `MYSQL_HOST`：数据库地址
- `MYSQL_PORT`：数据库端口
- `MYSQL_USER`：数据库用户名
- `MYSQL_PASSWORD`：数据库密码
- `MYSQL_DATABASE`：数据库名称

如果密码已存在系统环境变量中，可以不写在 `.env` 文件里，代码会自动从系统环境变量读取。

### Q2：Pydantic Settings 的 Config 内部类被弃用了？
**A：** 是的。Pydantic V2 中，`class Config` 写法已被弃用，应改用 `model_config = SettingsConfigDict(...)`。

**✅ 正确写法（V2）：**
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    MYSQL_HOST: str = "localhost"
    # ... 其他配置
```

### Q3：配置文件中开头定义的默认值和 .env 文件的关系是什么？

**A：** 读取优先级：**系统环境变量 > .env 文件 > 代码默认值**。
- 代码中的默认值是"兜底"机制，当环境变量和 `.env` 都没有时才生效。
- 注意：属性名必须全大写才能自动匹配同名的环境变量。

### Q4：`DATABASE_URL` 方法为什么用全大写？
**A：** 
1. 遵循 PEP 8 命名约定：常量/配置项使用全大写。
2. 使用 `@property` 装饰器，使其可以像属性一样访问（`settings.DATABASE_URL`）。

---

## 二、数据库连接相关

### Q5：SQLAlchemy 2.0 中 `SessionLocal` 和 `SessionFactory` 是什么关系？
**A：** 本质上是同一回事。
- `sessionmaker` 是 SQLAlchemy 提供的**工厂类**。
- `SessionLocal = sessionmaker(...)` 是我们创建的**工厂实例**。
- 命名为 `SessionLocal` 或 `SessionFactory` 都可以，FastAPI 社区约定俗成使用 `SessionLocal`。

### Q6：`get_db()` 函数中的 `try...finally` 和 `yield db` 是做什么的？
**A：**
- `yield db`：将数据库会话交给业务代码使用，函数在此**暂停**。
- `try...finally`：确保无论业务代码成功还是报错，`finally` 中的 `db.close()` 都会执行，归还数据库连接到连接池，防止资源泄漏。

**时序图：**
```
SessionLocal() 创建连接 → yield db（暂停，交出去）→ 业务代码执行 → 回到函数执行 finally → db.close()
```

### Q7：`server_default` 和 `default` 有什么区别？
**A：**
| 特性 | `server_default` | `default` |
|------|------------------|-----------|
| 生效位置 | 数据库层面（生成 DEFAULT 约束） | Python 应用层面 |
| 适用场景 | 希望数据库保证默认值（如时间戳） | 默认值依赖 Python 函数（如 `uuid.uuid4()`） |
| 对代码可见性 | 需 `refresh()` 后才能看到 | 创建实例后立即可见 |

**结论：** 对于 `created_at`、`updated_at` 等时间戳字段，使用 `server_default=func.now()` 更稳妥。

### Q8：`Base.metadata.create_all()` 的"表存在则跳过"效果是哪个参数控制的？
**A：** 这是 `create_all()` 方法的**默认行为**，不需要额外参数。
- 会先检查表是否存在，存在则跳过，不存在才创建。
- **不会自动修改已有表结构**，如需修改表结构，应使用 Alembic 或手动执行 SQL。

---

## 三、数据模型与 Schema 相关

### Q9：`schemas` 这个词怎么理解？`BaseModel` 和数据库的 `Base` 有联系吗？
**A：**
- **Schema**：中文翻译为"模式"或"结构"，用于定义 API 数据的格式。
- **两者完全没有联系**：

| 对比项 | `app.db.base.Base` | `pydantic.BaseModel` |
|--------|-------------------|---------------------|
| 来源 | SQLAlchemy | Pydantic |
| 用途 | 数据库表结构的基类 | API 数据结构的基类 |
| 产物 | 数据库中的表 | JSON 数据 |

### Q10：继承 `BaseModel` 主要用了哪些功能？
**A：**
1. **类型校验**：自动校验字段类型是否正确。
2. **数据转换**：自动将能转换的类型转过去。
3. **生成 JSON Schema**：FastAPI 自动生成 Swagger 文档。
4. **ORM 对象转换**：通过 `model_config = ConfigDict(from_attributes=True)` 实现。
5. **数据序列化**：`.model_dump_json()` 转为 JSON 字符串。

### Q11：为什么要写多个 Schema 类（如 `CategoryCreate`、`CategoryResponse`）？
**A：** 创建时和返回时需要的数据字段不同。
- **创建**：只需要 `name`（id 由数据库生成）。
- **返回**：需要 `id` + `name`。

通过继承 `Base` 类避免重复定义相同字段：
```python
class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
```

### Q12：`ConfigDict(from_attributes=True)` 是做什么的？
**A：** 允许 Pydantic 从 ORM 对象（SQLAlchemy 模型）自动转换数据。没有这个配置，将 ORM 对象传给 Pydantic 模型会报错。

---

## 四、API 路由相关

### Q13：API 版本号（如 `/api/v1/`）是做什么的？
**A：** 为了未来升级 API 时不影响旧客户端。
- `/api/v1/knowledge`：第一版 API
- `/api/v2/knowledge`：第二版 API（字段或逻辑可能有变化）

这是一个好习惯，不增加复杂度但为未来留有余地。

### Q14：各种请求体/响应体是如何被 API "调用"的？
**A：** 通过**类型提示**告诉 FastAPI，FastAPI 会自动完成校验和转换。

**示例：**
```python
@router.post("/", response_model=schemas.CategoryResponse)
def create_category(
    category_in: schemas.CategoryCreate,  # ← 请求体类型
    db: Session = Depends(get_db),
):
    # ...
```

**数据流向：**
```
前端 JSON → FastAPI 自动校验（CategoryCreate）→ CRUD 函数 → 数据库
数据库返回 ORM 对象 → FastAPI 自动转换（CategoryResponse）→ 前端 JSON
```

---

## 五、模块化思维

### Q15：实际开发中如何养成模块化思维？
**A：** 核心原则：**把"会一起变的东西放一起，不会一起变的东西分开"。**

**方法1：写代码前问自己三个问题**
| 问题 | 对应模块 |
|------|----------|
| 和"数据怎么存"有关？ | `models.py` |
| 和"数据怎么校验/传输"有关？ | `schemas.py` |
| 和"业务规则"有关？ | `crud.py` |
| 和"HTTP 请求/响应"有关？ | `endpoints/*.py` |

**方法2：用"如果我要换掉它"来测试边界**
| 假设场景 | 应该只改哪个模块？ |
|----------|-------------------|
| 数据库从 MySQL 换成 PostgreSQL | `config.py` + `session.py` |
| 分类表增加一个字段 | `models.py` + `schemas.py` |
| 创建分类前需要检查权限 | `crud.py` |
| API 路径变更 | `endpoints/*.py` |

**方法3：先写成一坨，感觉到痛了再拆**
这是真实的学习路径。痛点是模块化的最佳老师。

---

## 六、注意事项速查

### ⚠️ Pydantic V2 变化
- `class Config` → `model_config = SettingsConfigDict(...)`
- `BaseSettings` 从 `pydantic` 移到 `pydantic_settings`
- `orm_mode` → `from_attributes`

### ⚠️ 文件结构约定
```
src/app/
├── core/config.py       # 配置管理
├── db/                  # 数据库连接
├── models/              # ORM 模型（表结构）
├── schemas/             # Pydantic 模型（API 数据格式）
├── crud/                # 业务逻辑（增删改查）
└── api/v1/endpoints/    # API 路由
```

### ⚠️ 必须导入所有模型
在 `main.py` 中必须导入所有模型类，否则 `Base.metadata.create_all()` 不知道要创建哪些表：
```python
from app.models import Category, Knowledge
```

### ⚠️ 环境变量读取
- `.env` 文件中的变量名必须全大写
- 密码等敏感信息建议用系统环境变量，不写入 `.env`

### ⚠️ Git 提交节点建议
| 完成内容 | 提交信息示例 |
|----------|-------------|
| 配置 + 数据库模块 | `feat: 完成项目基础配置与数据库连接模块` |
| 模型 + Schema | `feat: 添加数据模型和 Pydantic Schema` |
| CRUD + API | `feat: 完成知识库增删改查 API 全部功能` |

---

## 七、API 接口速查表

### 分类管理 - `/api/v1/categories`
| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/` | 创建分类 |
| GET | `/` | 获取分类列表（支持分页） |
| GET | `/{id}` | 获取单个分类 |
| PUT | `/{id}` | 更新分类名称 |
| DELETE | `/{id}` | 删除分类 |

### 知识管理 - `/api/v1/knowledge`
| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/` | 创建知识条目 |
| GET | `/` | 获取知识列表（分页+分类筛选） |
| GET | `/{id}` | 获取单条知识 |
| PUT | `/{id}` | 更新知识（支持部分更新） |
| DELETE | `/{id}` | 删除知识 |

### 请求体示例
**创建分类：**
```json
{ "name": "技术文档" }
```

**创建知识：**
```json
{
    "title": "FastAPI 入门",
    "content": "FastAPI 是一个现代 Web 框架...",
    "category_id": 1
}
```

**更新知识（部分更新）：**
```json
{
    "title": "新标题"
}
```

---

## 八、常用命令速查

| 命令 | 用途 |
|------|------|
| `uvicorn app.main:app --reload` | 启动开发服务器 |
| `pip install -e .` | 安装项目依赖（使用 pyproject.toml） |
| `git add .` | 添加所有变更到暂存区 |
| `git commit -m "feat: xxx"` | 提交变更 |
| `git push` | 推送到远程仓库 |

---

*笔记生成时间：2026-04-16*
*项目：FastAPI 知识库练手项目*
```

---
作者：Mjolnir
```