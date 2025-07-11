# create new repository - https://github.com/tgilbert14/timothy-gilbert-portfolio
# go to settings > pages > Choose your branch (usually main) and root (/)
# Hit Save — this will generate your site URL

# set working directory to this files path
setwd(dirname(rstudioapi::getActiveDocumentContext()[[2]]))
# creates template for website
quarto::quarto_create_project("timothy-portfolio", type = "website")

# git bash commands to push to GitHub
git init
git add .
git commit -m "Initial Quarto site"
git remote add origin https://github.com/tgilbert14/timothy-gilbert-portfolio.git
git push -u origin main



git commit --allow-empty -m "Trigger rebuild"
git push

