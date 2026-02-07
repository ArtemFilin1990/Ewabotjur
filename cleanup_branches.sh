#!/bin/bash

# Скрипт для удаления всех веток кроме main
# Script to delete all branches except main

set -e

echo "🔍 Текущие ветки в репозитории:"
echo "Current branches in repository:"
git branch -a

echo ""
echo "⚠️  ВНИМАНИЕ: Этот скрипт удалит все ветки кроме main"
echo "WARNING: This script will delete all branches except main"
echo ""
echo "Ветки для удаления / Branches to delete:"
echo "  - copilot/fix-merge-conflict"
echo "  - copilot/update-documentation-files"
echo "  - claude/remove-other-branches"
echo ""

read -p "Продолжить? (yes/no): " -r
echo
if [[ ! $REPLY =~ ^[Yy]es$ ]]
then
    echo "❌ Отменено / Cancelled"
    exit 1
fi

echo "🗑️  Удаление удаленных веток..."
echo "Deleting remote branches..."

# Удаление удаленных веток
branches_to_delete=(
    "copilot/fix-merge-conflict"
    "copilot/update-documentation-files"
    "claude/remove-other-branches"
)

for branch in "${branches_to_delete[@]}"
do
    echo "  Удаление / Deleting: $branch"
    if git push origin --delete "$branch" 2>/dev/null; then
        echo "  ✅ Удалена удаленная ветка / Deleted remote branch: $branch"
    else
        echo "  ⚠️  Ветка не найдена на удаленном сервере / Branch not found on remote: $branch"
    fi

    # Удаление локальной ветки если она существует
    if git show-ref --verify --quiet "refs/heads/$branch"; then
        echo "  Удаление локальной ветки / Deleting local branch: $branch"
        git branch -D "$branch" 2>/dev/null || true
        echo "  ✅ Удалена локальная ветка / Deleted local branch: $branch"
    fi
done

echo ""
echo "✅ Очистка завершена!"
echo "Cleanup completed!"
echo ""
echo "📋 Оставшиеся ветки / Remaining branches:"
git branch -a

echo ""
echo "💡 Рекомендация: Переключитесь на ветку main"
echo "Recommendation: Switch to main branch"
echo "   git checkout main"
echo "   git pull origin main"
