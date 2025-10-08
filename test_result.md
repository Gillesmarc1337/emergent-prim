#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: |
  L'utilisateur a demandé d'ajouter de nouveaux blocs dans l'onglet "Projections":
  
  1. Nouveau bloc "Hot deals closing in the next 2 weeks to 30 days":
     - Tous les deals en B Legals
     - Fonctionnalité drag & drop pour réorganiser
     - Boutons pour masquer temporairement de la vue
  
  2. Nouveau bloc "Additional Hot leads that will most likely close within the next 3 months":
     - Tous les deals sur C Proposal sent et D POA Booked
     - Drag & drop capability
     - Tableau avec MRR et ARR
     - Bouton reset pour recharger les leads
  
  3. Corriger les blocs Performance Summary pour utiliser les mêmes données que le dashboard
  
  4. Améliorer les blocs Closing Projections pour mettre en évidence les upcoming meetings et weighted pipe

backend:
  - task: "Hot Deals API endpoint"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "Created /api/projections/hot-deals endpoint that filters deals in B Legals stage. Returns deal data with id, client, pipeline, MRR/ARR, owner, stage, and hubspot_link."

  - task: "Hot Leads API endpoint"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "Created /api/projections/hot-leads endpoint that filters deals in C Proposal sent and D POA Booked stages. Returns comprehensive deal data for MRR/ARR table display."

  - task: "Performance Summary API endpoint"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "Created /api/projections/performance-summary endpoint that uses the same calculation logic as dashboard for YTD revenue, targets, and forecast gap detection."

frontend:
  - task: "Hot Deals drag & drop interface"
    implemented: true
    working: true
    file: "/app/frontend/src/App.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
        - working: true
          agent: "main"
          comment: "Added DragDropContext with draggable deal items. Includes drag & drop reordering, hide functionality with X buttons, and reset button. Uses @hello-pangea/dnd library."

  - task: "Hot Leads table with MRR/ARR"
    implemented: true
    working: true
    file: "/app/frontend/src/App.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
        - working: true
          agent: "main"
          comment: "Created comprehensive table displaying MRR and ARR for hot leads with drag & drop functionality and reset button."

  - task: "Enhanced Performance Summary"
    implemented: true
    working: true
    file: "/app/frontend/src/App.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
        - working: true
          agent: "main"
          comment: "Updated Performance Summary section to use data from new API endpoint that matches dashboard calculations."

  - task: "Enhanced Closing Projections"
    implemented: true
    working: true
    file: "/app/frontend/src/App.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
        - working: true
          agent: "main"
          comment: "Enhanced Closing Projections with colored cards, weighted value highlighting, and upcoming high-priority meetings section."

metadata:
  created_by: "main_agent"
  version: "1.0"
  test_sequence: 0
  run_ui: true

test_plan:
  current_focus:
    - "Hot Deals drag & drop interface"
    - "Hot Leads table with MRR/ARR"
    - "Enhanced Performance Summary"
    - "Enhanced Closing Projections"
  stuck_tasks: []
  test_all: true
  test_priority: "high_first"

agent_communication:
    - agent: "main"
      message: "Implemented dynamic dashboard blocks with targets as requested. Backend API works correctly with month_offset parameter. Frontend displays ratios correctly. Need to test month navigation functionality and verify blocks update when changing months using Previous/Next Month buttons."
    - agent: "testing"
      message: "✅ BACKEND TESTING COMPLETE: All dynamic dashboard blocks functionality working perfectly. Tested /api/analytics/monthly with month_offset=0,1,2,3 - all return correct periods (Oct 2025, Sep 2025, Aug 2025, Jul 2025). Dashboard blocks contain all required fields with correct fixed targets. API structure matches requirements exactly. Backend implementation is solid and ready for production."