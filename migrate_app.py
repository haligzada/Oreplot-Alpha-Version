#!/usr/bin/env python3
"""
Migration script to integrate navigation into app.py
"""

# Read the backup file
with open('app_backup.py', 'r') as f:
    lines = f.readlines()

# New imports to add after the existing imports
new_imports = """
# Import page modules
from pages.dashboard_page import render_dashboard
from pages.projects_page import render_projects_page
from pages.reports_page import render_reports_page
from pages.profile_page import render_profile_page
from pages.account_settings_page import render_account_settings_page
from pages.app_settings_page import render_app_settings_page
from pages.billing_page import render_billing_page
from pages.team_page import render_team_page
from components.navigation import render_top_navigation, render_user_menu_dropdown
"""

# Find where to insert navigation setup
auth_line_idx = None
for i, line in enumerate(lines):
    if line.strip().startswith('current_user = require_auth()'):
        auth_line_idx = i
        break

# Find where CSS ends
css_end_idx = None
for i, line in enumerate(lines):
    if '"", unsafe_allow_html=True)' in line and i > 100:
        css_end_idx = i
        break

# Build the new file
output_lines = []

# Add lines up to and including TemplateManager import
for i, line in enumerate(lines):
    output_lines.append(line)
    if 'from template_manager import TemplateManager' in line:
        output_lines.append(new_imports)
        break

# Continue with the rest until auth line
start_idx = len(output_lines)
for i in range(start_idx, auth_line_idx + 1):
    output_lines.append(lines[i])

# Add navigation setup
output_lines.append('\n')
output_lines.append('# Initialize current_page in session state if not set\n')
output_lines.append("if 'current_page' not in st.session_state:\n")
output_lines.append("    st.session_state.current_page = 'dashboard'\n")
output_lines.append('\n')
output_lines.append('# Render top navigation and get current page\n')
output_lines.append('current_page = render_top_navigation()\n')
output_lines.append('\n')
output_lines.append('# Render user menu in sidebar\n')
output_lines.append('render_user_menu_dropdown(current_user)\n')
output_lines.append('\n')

# Add lines from after auth to CSS end
for i in range(auth_line_idx + 1, css_end_idx + 1):
    if 'render_user_info()' not in lines[i]:  # Skip old user info call
        output_lines.append(lines[i])

# Add page routing
output_lines.append('\n')
output_lines.append('# Page Routing Logic\n')
output_lines.append("if current_page == 'dashboard':\n")
output_lines.append('    render_dashboard(current_user)\n')
output_lines.append('\n')
output_lines.append("elif current_page == 'projects':\n")
output_lines.append('    render_projects_page(current_user)\n')
output_lines.append('\n')
output_lines.append("elif current_page == 'reports':\n")
output_lines.append('    render_reports_page(current_user)\n')
output_lines.append('\n')
output_lines.append("elif current_page == 'profile':\n")
output_lines.append('    render_profile_page(current_user)\n')
output_lines.append('\n')
output_lines.append("elif current_page == 'account_settings':\n")
output_lines.append('    render_account_settings_page(current_user)\n')
output_lines.append('\n')
output_lines.append("elif current_page == 'app_settings':\n")
output_lines.append('    render_app_settings_page(current_user)\n')
output_lines.append('\n')
output_lines.append("elif current_page == 'billing':\n")
output_lines.append('    render_billing_page(current_user)\n')
output_lines.append('\n')
output_lines.append("elif current_page == 'team':\n")
output_lines.append('    render_team_page(current_user)\n')
output_lines.append('\n')
output_lines.append("elif current_page == 'ai_agent':\n")
output_lines.append('    # AI Agent page - existing functionality\n')

# Add all remaining lines with proper indentation (4 spaces)
for i in range(css_end_idx + 1, len(lines)):
    line = lines[i]
    # Add 4 spaces of indentation for all lines in AI agent
    if line.strip():  # Non-empty lines
        output_lines.append('    ' + line)
    else:  # Empty lines
        output_lines.append(line)

# Write the new file
with open('app.py', 'w') as f:
    f.writelines(output_lines)

print("Migration completed successfully!")
print(f"Total lines: {len(output_lines)}")
