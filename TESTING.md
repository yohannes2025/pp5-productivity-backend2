# Testing

## Table of Contents

- [Testing](#testing)
  - [Table of Contents](#table-of-contents)
  - [Testing Summary](#testing-summary)
  - [Manual Testing](#manual-testing)
    - [`productivity_app/models.py`](#productivity_appmodelspy)
    - [`productivity_app/permissions.py`](#productivity_apppermissionspy)
    - [`productivity_app/serializers.py`](#productivity_appserializerspy)
    - [`productivity_app/views.py`](#productivity_appviewspy)
    - [`drf_api/urls.py`](#drf_apiurlspy)
  - [Automated Tests](#automated-tests)
  - [Python Validation](#python-validation)
    - [Tools Used](#tools-used)
    - [Validation Results](#validation-results)
  - [Resolved Bugs](#resolved-bugs)
  - [Unresolved Bugs](#unresolved-bugs)

---

## Testing Summary

A **comprehensive test suite** was implemented using **Django’s TestCase** and **DRF’s APITestCase**.  
All components were tested: **models, permissions, serializers, views, and integration flows**.

**All tests pass with 100% success**  
**All PEP-8 violations fixed**  
**All known bugs resolved**

---

## Manual Testing

### `productivity_app/models.py`

| Test                                                 | Result  |
| ---------------------------------------------------- | ------- |
| Task creation (required + optional fields)           | Success |
| Default `status='pending'` applied                   | Success |
| `created_at` / `updated_at` auto-populated           | Success |
| `__str__()` returns title                            | Success |
| `is_overdue` property works (past/future/today/null) | Success |
| `assigned_users` many-to-many relationship           | Success |
| File upload + cascade delete                         | Success |
| Profile auto-created via signal                      | Success |

### `productivity_app/permissions.py`

| Permission             | Expected Behavior               | Result  |
| ---------------------- | ------------------------------- | ------- |
| `IsAssignedOrReadOnly` | Read: all, Write: only assigned | Success |
| `IsSelfOrReadOnly`     | Only modify own user            | Success |
| `IsOwnerOrReadOnly`    | Only modify own profile         | Success |

### `productivity_app/serializers.py`

- All serializers tested with valid/invalid data
- Nested relationships (`upload_files`, `assigned_users`) correct
- `RegisterSerializer`: password match, strength, duplicate checks
- `TaskDetailSerializer`: `assigned_user_ids` saves correctly

### `productivity_app/views.py`

| Endpoint                    | Auth    | Action       | Result                |
| --------------------------- | ------- | ------------ | --------------------- |
| `/api/register/`            | None    | POST valid   | 201 + JWT             |
| `/api/login/`               | None    | POST valid   | 200 + JWT             |
| `/api/tasks/`               | Auth    | GET          | Only assigned tasks   |
| `/api/tasks/`               | Unauth  | GET          | All tasks (read-only) |
| `/api/tasks/{id}/`          | Auth    | PATCH/DELETE | Only if assigned      |
| `/api/profiles/`            | Auth    | PATCH own    | Success               |
| `/api/profiles/{id}/`       | Auth    | PATCH other  | 403                   |
| File upload via `new_files` | Success |

### `drf_api/urls.py`

- Root `/` → welcome message
- All API routes accessible and return correct status codes

---

## Automated Tests

| File                  | Tests | Coverage                     | Status      |
| --------------------- | ----- | ---------------------------- | ----------- |
| `test_models.py`      | 12    | Models + signals             | Success All |
| `test_permissions.py` | 4     | All custom permissions       | Success All |
| `test_serializers.py` | 5     | All serializers + validation | Success All |
| `test_views.py`       | 11    | All ViewSets + APIViews      | Success All |
| `test_integration.py` | 3     | Full registration flow       | Success All |

**Total: 35 automated tests → All passing**

---

## Python Validation

### Tools Used

- **CI Python Linter**
- **flake8** → Linting (E501, W291, etc. fixed)
- **Django Test Runner** → 100% pass rate

### Validation Results

| Component   | Validation Method       | Result              |
| ----------- | ----------------------- | ------------------- |
| Models      | Unit tests + shell      | Success             |
| Permissions | `APIRequestFactory`     | Success             |
| Serializers | DRF serializer tests    | Success             |
| Views       | `APIClient` + auth      | Success             |
| Integration | End-to-end registration | Success             |
| Code Style  | flake8                  | **Zero violations** |

---

## Resolved Bugs

| Bug                                       | Location               | Fix                                                |
| ----------------------------------------- | ---------------------- | -------------------------------------------------- |
| `UNIQUE constraint failed: category.name` | All test files         | Used `get_or_create()` in `setUp()`                |
| Past `due_date` not rejected              | `TaskSerializer`       | Added `task.full_clean()` in `create()`/`update()` |
| `assigned_user_ids` not saving            | `TaskDetailSerializer` | Correct `source=` and write-only field             |
| JWT not returned on register              | `RegisterViewSet`      | Proper `RefreshToken.for_user()`                   |
| Profile not created on register           | Signal                 | Fixed `create_profile` signal                      |
| PEP-8 E501 line too long                  | Multiple files         | Reformatted with **Black**                         |
| Commented-out code                        | `models.py`            | Removed                                            |
| Test file named `.py.py`                  | `test_integration.py`  | Renamed + added real tests                         |

**All bugs fixed. No regression.**

---

## Unresolved Bugs

**None**

The application is **fully functional**, **secure**, **tested**, and **PEP-8 compliant**.

---
