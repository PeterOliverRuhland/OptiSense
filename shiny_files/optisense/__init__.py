"""OptiSense – teaching tool for LP, ILP and MILP with two variables.

pages/   the three pages, each with its texts, layout and server part:
         work (“Model & solution”, start page), learn (“Learn & practise”), guide (“Guide”)
core/    maths of the start page: model, solver, sensitivity, LP format (no Shiny)
i18n/    translation (English, German); texts shared by the pages in common.py
ui/      the frame around the pages: navbar, language switch, styles and scripts
server/  one AppContext per session (language, the problem) that the pages share
config   limits, default names and design-system colours
"""
