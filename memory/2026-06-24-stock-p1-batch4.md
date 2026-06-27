---
name: 2026-06-24-stock-p1-batch4
description: Stock P1-3 schema.py → pydantic.BaseModel 重构闭环 — 17 dataclass 迁移 + validator.py API 适配 + pytest 177 零回归
metadata:
  node_type: memory
  type: project
  originSessionId: 3bf0438c-1772-45ab-8cc3-98e83108d55d
---

# 2026-06-24 Stock P1-3 schema.py pydantic 重构闭环

## 完成项（1 commit）

| commit | 任务 | 改动 | 行数 |
|--------|------|------|------|
| `583febb` | **P1-3** refactor(data_layer) | 4 文件：schema.py + validator.py + test_schema.py + test_validator.py | +106/-94 |

## 关键改动

### 1. data_layer/schema.py（17 @dataclass → BaseModel）
- 所有 17 个 dataclass（RawDailySchema / RawFinaIndicatorSchema / RawStockBasicSchema 等）改为 `class X(BaseModel)`
- **公共接口完全兼容**：`X(field=value)` 实例化、`inst.field` 访问、`COLLECTION_SCHEMAS[path]` 字典保持不变
- `Optional[float] = None` 在 pydantic v2 中直接支持，无需改成 `float | None`

### 2. data_layer/validator.py（适配 pydantic v2 API）
- `is_dataclass(schema_class)` → `_is_pydantic_model()`（`issubclass(cls, BaseModel)`）
- `dataclasses.fields(schema_class)` → `schema_class.model_fields`（dict-like）
- `field_info.type` → `field_info.annotation`
- `MISSING` → `PydanticUndefined`（pydantic v2）
- `_check_field_type(value, field_info)` → `_check_field_type(value, field_name, expected_type)`：因为 **FieldInfo 没有 `.name` 属性**（pydantic v2 API 变化）

### 3. tests/test_data_layer/test_schema.py
- `is_dataclass(schema)` → `issubclass(schema, BaseModel)`
- `fields(schema)` → `schema.model_fields`
- 测试断言 `f_names = set(schema.model_fields.keys())`

### 4. tests/test_data_layer/test_validator.py
- `_SampleSchema` / `_StrictSchema` 从 `@dataclass` 改为 `BaseModel`
- 测试期望 `validate_schema` 接收 BaseModel instance 而非 dataclass

## 关键陷阱（pydantic v2 vs dataclass）

| 陷阱 | dataclass 行为 | pydantic v2 行为 | 影响 |
|------|---------------|------------------|------|
| 字段名访问 | `field_info.name` | **无** `.name`（用 dict key） | validator.py 必须改 API：把 `field_name` 作为参数传入 |
| 类型注解 | `field_info.type` | `field_info.annotation` | validator.py 改 |
| 默认值 sentinel | `MISSING` | `PydanticUndefined` | validator.py 改 |
| Optional[float] | `typing.Optional[float]` | `typing.Optional[float]`（保持） | 无影响 |
| 实例化（部分字段） | `X(field=value)` | 同样 | 公共接口兼容 |
| 字段 metadata | `dataclasses.field()` | `Field(...)` | 本次不涉及 |
| mutability | 默认 mutable | BaseModel 默认 mutable + frozen 可选 | 无影响 |

## 零回归验证

- `pytest tests/ -q` → **177 passed / 0 failed**（基线保持）
- `ruff check data_layer/validator.py data_layer/schema.py tests/test_data_layer/` → **0 errors**
- git status 仅剩用户文件（CLAUDE.md / PATCH_C / bak / memos / portfolio_state）

## 已知问题（未在本次修复，记录在案）

1. **`RawLimitListSchema` 未注册**：定义在 schema.py 但 `COLLECTION_SCHEMAS` 没注册它（17 schema 定义 vs 16 注册）
2. **`validate_dataframe_schema` 的 lazy validation 设计**：`_field_has_default` 在 `required_only` 检查后仍跳过 → 有默认值字段永远不进 `date_cols` / `required_cols`，日期类型检查走通用 `object/str` 分支而非专用 `应为 int` 分支
3. **`validator.py` 的手写校验仍保留**：理论上 pydantic 的 `model_validate` + `@field_validator` 可以替代 `validate_schema` 函数（130 行手写代码），但本次只做 API 适配，不做行为替换（避免越界改架构）

**Why:** CLAUDE.md 代码复用原则明确禁止重复造轮子——pydantic 已加入 pyproject.toml 依赖（2026-06-24 P0-2），应该优先使用 pydantic 而非手写 dataclass + 校验逻辑。
**How to apply:**
- 任何新数据契约 schema 直接用 `BaseModel` 而非 `@dataclass`
- validator.py 的工具函数可继续保留（向后兼容 dict/instance 双模式），但新增校验建议用 `model_validate`
- 适配 pydantic v2 API 时注意 `field_info` 没有 `.name` 属性，必须从外部传字段名
- `Optional[T] = None` 在 pydantic v2 中无需改成 `T | None`，直接支持
关联：[[2026-06-24-stock-p1-batch3]]（P1-1.1 test_data_layer），[[2026-06-24-stock-p0-3-execution]]（pydantic 依赖引入）。