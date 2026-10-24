@echo off
chcp 65001 >nul
cd /d "%~dp0"
title PPT_agent git 初始化

echo ========================================
echo    PPT_agent  Git 初始化
echo ========================================
echo.

where git >nul 2>nul
if errorlevel 1 (
  echo [错误] 未检测到 git，请先安装 Git for Windows：
  echo https://git-scm.com/download/win
  echo.
  pause
  exit /b 1
)

if not exist .git (
  echo [1/4] 初始化仓库 ...
  git init
) else (
  echo [1/4] 已存在 .git，跳过初始化
)

echo [2/4] 配置本地仓库参数 ...
git config core.autocrlf false
git config core.quotepath false

echo [3/4] 统一主分支名为 main ...
git branch -M main

echo [4/4] 首次提交 ...
git add -A
git diff --cached --quiet
if errorlevel 1 (
  git commit -m "chore: 初始化 PPT_agent 项目骨架与协作规范"
) else (
  echo 没有需要提交的新内容
)

echo.
echo ========================================
echo    初始化完成
echo ========================================
echo 当前分支：
git branch --show-current
echo.
echo 最近提交：
git log --oneline -5
echo.
echo 下一步（参考 .ai/git-workflow.md）：
echo  1. 在 Gitee（推荐，国内快）或 GitHub 新建一个【空私有仓库】
echo     （不要勾选初始化 README/.gitignore/license）
echo  2. 关联远程并推送（把下面地址换成你的）：
echo     git remote add origin https://你的仓库地址
echo     git push -u origin main
echo.
pause
