# Branch Cleanup Instructions

## Цель
Оставить только ветку `main`, удалив все остальные ветки.

## Текущее состояние веток
- ✅ `main` - основная ветка (сохранить)
- ❌ `claude/remove-other-branches` - текущая рабочая ветка (удалить после слияния)
- ❌ `copilot/fix-merge-conflict` - удалить
- ❌ `copilot/update-documentation-files` - удалить

## Инструкции по удалению веток

### Вариант 1: Через GitHub Web Interface
1. Перейдите на страницу: https://github.com/ArtemFilin1990/Ewabotjur/branches
2. Для каждой ветки (кроме `main`) нажмите кнопку удаления (корзина)

### Вариант 2: Через командную строку
```bash
# Удалить удаленные ветки
git push origin --delete copilot/fix-merge-conflict
git push origin --delete copilot/update-documentation-files
git push origin --delete claude/remove-other-branches

# Удалить локальные ветки (если они есть)
git branch -D copilot/fix-merge-conflict
git branch -D copilot/update-documentation-files
git branch -D claude/remove-other-branches
```

### Вариант 3: Использовать скрипт cleanup_branches.sh
```bash
chmod +x cleanup_branches.sh
./cleanup_branches.sh
```

## После удаления
После удаления всех веток кроме `main`:
1. Переключитесь на ветку `main`: `git checkout main`
2. Обновите локальный репозиторий: `git pull origin main`
3. Проверьте список веток: `git branch -a`

Должна остаться только ветка `main`.
