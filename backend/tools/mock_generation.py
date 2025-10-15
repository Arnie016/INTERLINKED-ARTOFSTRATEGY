"""
Mock data generation tool for organizational intelligence.

This module generates realistic mock data for various organizational data sources
including Slack, email, calendars, documents, project management, version control,
and more. The generated data can be used by agents to create Neo4j nodes and relationships.
"""

import json
import random
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path

# Try to import Faker, fallback to basic generation if not available
try:
    from faker import Faker
    FAKER_AVAILABLE = True
except ImportError:
    FAKER_AVAILABLE = False
    print("Warning: Faker library not available. Using basic name generation.")


class OrganizationalDataGenerator:
    """Generates realistic mock organizational data."""
    
    def __init__(self, company_name: str, company_size: str = "medium"):
        """
        Initialize the data generator.
        
        Args:
            company_name: Name of the company
            company_size: Size of company (small: 10-50, medium: 50-200, large: 200-1000)
        """
        self.company_name = company_name
        self.company_size = company_size
        
        if FAKER_AVAILABLE:
            self.fake = Faker()
        else:
            self.fake = None
        
        # Define company size parameters
        self.size_params = {
            "small": {
                "employees": random.randint(10, 50),
                "departments": random.randint(3, 6),
                "projects": random.randint(5, 15),
                "systems": random.randint(3, 8)
            },
            "medium": {
                "employees": random.randint(50, 200),
                "departments": random.randint(6, 12),
                "projects": random.randint(15, 40),
                "systems": random.randint(8, 20)
            },
            "large": {
                "employees": random.randint(200, 1000),
                "departments": random.randint(12, 25),
                "projects": random.randint(40, 100),
                "systems": random.randint(20, 50)
            }
        }
        
        self.params = self.size_params.get(company_size, self.size_params["medium"])
        
        # Data storage
        self.employees = []
        self.departments = []
        self.projects = []
        self.systems = []
        self.processes = []
        
        # Relationship storage
        self.relationships = {
            "reporting": [],
            "collaboration": [],
            "project_assignments": [],
            "system_usage": [],
            "process_ownership": [],
            "department_membership": []
        }
        
        # Communication data
        self.slack_messages = []
        self.emails = []
        self.calendar_events = []
        self.document_interactions = []
        self.code_commits = []
        self.task_interactions = []
    
    def _generate_name(self) -> str:
        """Generate a realistic person name."""
        if self.fake:
            return self.fake.name()
        else:
            first_names = ["Alice", "Bob", "Carol", "David", "Emma", "Frank", "Grace", "Henry", 
                          "Isabel", "Jack", "Kate", "Leo", "Maria", "Nathan", "Olivia", "Peter",
                          "Quinn", "Rachel", "Sam", "Tina", "Uma", "Victor", "Wendy", "Xavier", "Yara", "Zack"]
            last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
                         "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
                         "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Thompson", "White"]
            return f"{random.choice(first_names)} {random.choice(last_names)}"
    
    def _generate_email(self, name: str) -> str:
        """Generate email from name."""
        clean_name = name.lower().replace(" ", ".")
        domain = self.company_name.lower().replace(" ", "")
        return f"{clean_name}@{domain}.com"
    
    def generate_departments(self) -> List[Dict[str, Any]]:
        """Generate department data."""
        dept_templates = [
            {"name": "Engineering", "budget_range": (500000, 2000000), "functions": ["Software Development", "DevOps", "QA"]},
            {"name": "Product", "budget_range": (300000, 1000000), "functions": ["Product Management", "Design", "Research"]},
            {"name": "Sales", "budget_range": (400000, 1500000), "functions": ["Enterprise Sales", "SMB Sales", "Sales Ops"]},
            {"name": "Marketing", "budget_range": (300000, 1200000), "functions": ["Content", "Demand Gen", "Brand"]},
            {"name": "Customer Success", "budget_range": (200000, 800000), "functions": ["Support", "Onboarding", "Account Management"]},
            {"name": "Finance", "budget_range": (200000, 600000), "functions": ["Accounting", "FP&A", "Payroll"]},
            {"name": "HR", "budget_range": (150000, 500000), "functions": ["Recruiting", "People Ops", "L&D"]},
            {"name": "Operations", "budget_range": (200000, 700000), "functions": ["IT", "Facilities", "Procurement"]},
            {"name": "Legal", "budget_range": (150000, 600000), "functions": ["Contracts", "Compliance", "IP"]},
            {"name": "Data & Analytics", "budget_range": (300000, 1000000), "functions": ["Data Engineering", "Analytics", "ML"]},
        ]
        
        num_depts = self.params["departments"]
        selected_depts = random.sample(dept_templates, min(num_depts, len(dept_templates)))
        
        for dept_template in selected_depts:
            budget_min, budget_max = dept_template["budget_range"]
            dept = {
                "name": dept_template["name"],
                "description": f"{dept_template['name']} department responsible for {', '.join(dept_template['functions'])}",
                "budget": random.randint(budget_min, budget_max),
                "headcount": random.randint(5, self.params["employees"] // num_depts + 10),
                "location": random.choice(["New York", "San Francisco", "Austin", "Remote", "London", "Singapore"]),
                "status": "active",
                "established_date": (datetime.now() - timedelta(days=random.randint(365, 3650))).isoformat(),
                "functions": dept_template["functions"]
            }
            self.departments.append(dept)
        
        return self.departments
    
    def generate_employees(self) -> List[Dict[str, Any]]:
        """Generate employee data with realistic roles and attributes."""
        if not self.departments:
            self.generate_departments()
        
        roles_by_dept = {
            "Engineering": ["Software Engineer", "Senior Engineer", "Engineering Manager", "Tech Lead", "Staff Engineer", "DevOps Engineer", "QA Engineer"],
            "Product": ["Product Manager", "Senior PM", "Product Designer", "UX Researcher", "Design Lead"],
            "Sales": ["Account Executive", "Sales Manager", "SDR", "Enterprise AE", "Sales Operations Analyst"],
            "Marketing": ["Marketing Manager", "Content Writer", "Marketing Analyst", "Demand Gen Specialist", "Brand Manager"],
            "Customer Success": ["Customer Success Manager", "Support Engineer", "Onboarding Specialist", "Account Manager"],
            "Finance": ["Financial Analyst", "Accountant", "Finance Manager", "Controller", "FP&A Analyst"],
            "HR": ["HR Manager", "Recruiter", "People Ops Specialist", "L&D Manager", "HR Business Partner"],
            "Operations": ["Operations Manager", "IT Administrator", "Facilities Manager", "Procurement Specialist"],
            "Legal": ["Legal Counsel", "Compliance Manager", "Contract Specialist", "Paralegal"],
            "Data & Analytics": ["Data Engineer", "Data Analyst", "ML Engineer", "Analytics Manager", "Data Scientist"]
        }
        
        levels = ["Junior", "Mid-level", "Senior", "Staff", "Principal", "Lead"]
        
        for dept in self.departments:
            dept_name = dept["name"]
            dept_headcount = dept["headcount"]
            dept_roles = roles_by_dept.get(dept_name, ["Specialist", "Manager", "Coordinator"])
            
            # Generate department head
            head_name = self._generate_name()
            employee = {
                "name": head_name,
                "email": self._generate_email(head_name),
                "role": f"{dept_name} Director",
                "department": dept_name,
                "level": random.choice(["Director", "VP", "Head of"]),
                "tenure_years": random.uniform(2, 10),
                "salary": random.randint(120000, 250000),
                "location": dept["location"],
                "skills": self._generate_skills(dept_name),
                "status": "active",
                "start_date": (datetime.now() - timedelta(days=random.randint(730, 3650))).isoformat()
            }
            self.employees.append(employee)
            dept["head"] = head_name
            
            # Generate department employees
            for _ in range(dept_headcount - 1):
                emp_name = self._generate_name()
                role = random.choice(dept_roles)
                
                # Add level prefix for some roles
                if random.random() > 0.4 and "Manager" not in role and "Director" not in role:
                    role = f"{random.choice(levels)} {role}"
                
                employee = {
                    "name": emp_name,
                    "email": self._generate_email(emp_name),
                    "role": role,
                    "department": dept_name,
                    "level": self._determine_level(role),
                    "tenure_years": random.uniform(0.5, 8),
                    "salary": random.randint(50000, 180000),
                    "location": dept["location"] if random.random() > 0.2 else random.choice(["Remote", "Hybrid"]),
                    "skills": self._generate_skills(dept_name),
                    "status": "active" if random.random() > 0.05 else "contractor",
                    "start_date": (datetime.now() - timedelta(days=random.randint(30, 2920))).isoformat()
                }
                self.employees.append(employee)
        
        return self.employees
    
    def _generate_skills(self, department: str) -> List[str]:
        """Generate realistic skills based on department."""
        skill_sets = {
            "Engineering": ["Python", "JavaScript", "React", "Node.js", "AWS", "Docker", "Kubernetes", "SQL", "Git", "CI/CD"],
            "Product": ["Product Strategy", "User Research", "Roadmapping", "Agile", "SQL", "Analytics", "Figma", "A/B Testing"],
            "Sales": ["Salesforce", "Prospecting", "Negotiation", "Account Management", "CRM", "Sales Strategy"],
            "Marketing": ["SEO", "Content Marketing", "Google Analytics", "HubSpot", "Social Media", "Email Marketing", "Adobe Creative Suite"],
            "Customer Success": ["Customer Support", "Zendesk", "Intercom", "Account Management", "Onboarding", "Training"],
            "Finance": ["Excel", "Financial Modeling", "QuickBooks", "FP&A", "GAAP", "Financial Analysis"],
            "HR": ["Recruiting", "ATS Systems", "Employee Relations", "Performance Management", "HRIS", "Compliance"],
            "Operations": ["Project Management", "Process Optimization", "Supply Chain", "Vendor Management"],
            "Legal": ["Contract Law", "Compliance", "Risk Management", "Legal Research", "Negotiation"],
            "Data & Analytics": ["Python", "SQL", "Tableau", "Machine Learning", "Statistics", "ETL", "Data Modeling"]
        }
        
        base_skills = skill_sets.get(department, ["Communication", "Project Management", "Analysis"])
        return random.sample(base_skills, min(random.randint(3, 6), len(base_skills)))
    
    def _determine_level(self, role: str) -> str:
        """Determine employee level from role."""
        if any(word in role for word in ["Director", "VP", "Head"]):
            return "Executive"
        elif any(word in role for word in ["Manager", "Lead", "Principal", "Staff"]):
            return "Senior"
        elif "Senior" in role:
            return "Mid-Senior"
        elif "Junior" in role:
            return "Junior"
        else:
            return "Mid-level"
    
    def generate_projects(self) -> List[Dict[str, Any]]:
        """Generate project data."""
        if not self.employees:
            self.generate_employees()
        
        project_templates = [
            "Customer Portal Redesign", "API v2 Migration", "Mobile App Launch",
            "Data Warehouse Implementation", "Security Audit", "Product Feature: {}",
            "Process Automation: {}", "System Integration: {}", "Marketing Campaign: {}",
            "Sales Enablement Platform", "Employee Onboarding System", "Analytics Dashboard"
        ]
        
        for _ in range(self.params["projects"]):
            template = random.choice(project_templates)
            if "{}" in template:
                template = template.format(random.choice(["Q1", "Q2", "Q3", "Q4", "2024", "2025"]))
            
            start_date = datetime.now() - timedelta(days=random.randint(0, 365))
            duration_days = random.randint(30, 365)
            end_date = start_date + timedelta(days=duration_days)
            
            project = {
                "name": template,
                "description": f"Strategic project for {template.lower()}",
                "status": random.choice(["planning", "active", "active", "completed", "on-hold"]),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "budget": random.randint(50000, 1000000),
                "priority": random.choice(["low", "medium", "medium", "high", "critical"]),
                "department": random.choice(self.departments)["name"],
                "sponsor": random.choice(self.employees)["name"],
                "manager": random.choice([e for e in self.employees if "Manager" in e["role"] or "Lead" in e["role"]])["name"],
                "team_size": random.randint(3, 15),
                "progress_percentage": random.randint(10, 95) if random.choice([True, False]) else 0
            }
            self.projects.append(project)
        
        return self.projects
    
    def generate_systems(self) -> List[Dict[str, Any]]:
        """Generate system/application data."""
        system_templates = [
            {"name": "Slack", "type": "communication", "vendor": "Slack Technologies", "criticality": "high"},
            {"name": "Google Workspace", "type": "productivity", "vendor": "Google", "criticality": "high"},
            {"name": "Salesforce", "type": "CRM", "vendor": "Salesforce", "criticality": "critical"},
            {"name": "Jira", "type": "project_management", "vendor": "Atlassian", "criticality": "high"},
            {"name": "GitHub", "type": "version_control", "vendor": "GitHub", "criticality": "critical"},
            {"name": "AWS", "type": "infrastructure", "vendor": "Amazon", "criticality": "critical"},
            {"name": "Zendesk", "type": "support", "vendor": "Zendesk", "criticality": "high"},
            {"name": "HubSpot", "type": "marketing", "vendor": "HubSpot", "criticality": "medium"},
            {"name": "Notion", "type": "knowledge_base", "vendor": "Notion", "criticality": "medium"},
            {"name": "Tableau", "type": "analytics", "vendor": "Tableau", "criticality": "medium"},
            {"name": "Workday", "type": "HRIS", "vendor": "Workday", "criticality": "high"},
            {"name": "Zoom", "type": "video_conferencing", "vendor": "Zoom", "criticality": "high"},
        ]
        
        num_systems = min(self.params["systems"], len(system_templates))
        selected_systems = random.sample(system_templates, num_systems)
        
        for sys_template in selected_systems:
            system = {
                "name": sys_template["name"],
                "type": sys_template["type"],
                "vendor": sys_template["vendor"],
                "version": f"{random.randint(1, 10)}.{random.randint(0, 20)}.{random.randint(0, 50)}",
                "status": random.choice(["active", "active", "active", "maintenance"]),
                "criticality": sys_template["criticality"],
                "owner": random.choice(self.employees)["name"],
                "department": random.choice(self.departments)["name"],
                "users_count": random.randint(5, len(self.employees)),
                "cost_annual": random.randint(5000, 200000),
                "implementation_date": (datetime.now() - timedelta(days=random.randint(365, 1825))).isoformat()
            }
            self.systems.append(system)
        
        return self.systems
    
    def generate_processes(self) -> List[Dict[str, Any]]:
        """Generate business process data."""
        if not self.departments:
            self.generate_departments()
        
        process_templates = {
            "Engineering": ["Code Review", "Sprint Planning", "Deployment", "Incident Response", "Technical Design Review"],
            "Product": ["Product Discovery", "User Research", "Feature Prioritization", "Release Planning"],
            "Sales": ["Lead Qualification", "Demo Scheduling", "Contract Negotiation", "Deal Review"],
            "Marketing": ["Content Approval", "Campaign Planning", "Lead Scoring", "Event Management"],
            "Customer Success": ["Customer Onboarding", "Ticket Escalation", "QBR Preparation", "Renewal Process"],
            "Finance": ["Invoice Processing", "Expense Approval", "Budget Review", "Month-End Close"],
            "HR": ["Candidate Screening", "Offer Approval", "Performance Review", "Employee Onboarding"],
            "Operations": ["Vendor Approval", "Access Provisioning", "Asset Management", "Compliance Check"],
        }
        
        for dept in self.departments:
            dept_name = dept["name"]
            dept_processes = process_templates.get(dept_name, ["Standard Process", "Review Process"])
            
            for proc_name in dept_processes:
                process = {
                    "name": f"{dept_name} - {proc_name}",
                    "description": f"{proc_name} process for {dept_name} department",
                    "category": dept_name,
                    "owner": random.choice([e for e in self.employees if e["department"] == dept_name])["name"],
                    "department": dept_name,
                    "frequency": random.choice(["daily", "weekly", "monthly", "quarterly", "as-needed"]),
                    "complexity": random.choice(["low", "medium", "medium", "high"]),
                    "automation_level": random.choice(["manual", "semi-automated", "automated"]),
                    "sla_hours": random.choice([2, 4, 8, 24, 48, 72]),
                    "status": "active",
                    "participants_count": random.randint(2, 10)
                }
                self.processes.append(process)
        
        return self.processes
    
    def generate_relationships(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generate relationship data between entities."""
        if not self.employees:
            self.generate_employees()
        if not self.projects:
            self.generate_projects()
        if not self.systems:
            self.generate_systems()
        if not self.processes:
            self.generate_processes()
        
        # Reporting relationships
        for dept in self.departments:
            dept_head = dept.get("head")
            dept_employees = [e for e in self.employees if e["department"] == dept["name"] and e["name"] != dept_head]
            
            for emp in dept_employees:
                # Some report to department head, others to managers
                if "Manager" in emp["role"] or "Lead" in emp["role"]:
                    manager = dept_head
                else:
                    managers = [e for e in dept_employees if "Manager" in e["role"] or "Lead" in e["role"]]
                    manager = random.choice(managers)["name"] if managers else dept_head
                
                self.relationships["reporting"].append({
                    "from": emp["name"],
                    "to": manager,
                    "type": "REPORTS_TO",
                    "relationship_type": random.choice(["direct", "direct", "direct", "matrix"]),
                    "start_date": emp["start_date"]
                })
        
        # Department membership
        for emp in self.employees:
            self.relationships["department_membership"].append({
                "from": emp["name"],
                "to": emp["department"],
                "type": "BELONGS_TO",
                "allocation_percentage": random.choice([100, 100, 100, 80, 50]),  # Most are 100%
                "start_date": emp["start_date"]
            })
        
        # Project assignments
        for project in self.projects:
            team_size = project["team_size"]
            # Prefer employees from the project's department
            dept_employees = [e for e in self.employees if e["department"] == project["department"]]
            other_employees = [e for e in self.employees if e["department"] != project["department"]]
            
            # 70% from same department, 30% from other departments
            same_dept_count = int(team_size * 0.7)
            other_dept_count = team_size - same_dept_count
            
            assigned = random.sample(dept_employees, min(same_dept_count, len(dept_employees)))
            if other_dept_count > 0:
                assigned += random.sample(other_employees, min(other_dept_count, len(other_employees)))
            
            for emp in assigned:
                self.relationships["project_assignments"].append({
                    "from": emp["name"],
                    "to": project["name"],
                    "type": "WORKS_ON",
                    "role": random.choice(["contributor", "lead", "reviewer"]),
                    "allocation_percentage": random.choice([25, 50, 75, 100]),
                    "start_date": project["start_date"]
                })
        
        # System usage
        for system in self.systems:
            # Different systems have different user patterns
            if system["type"] in ["communication", "productivity", "video_conferencing"]:
                # Most employees use these
                users = random.sample(self.employees, int(len(self.employees) * 0.9))
            elif system["type"] in ["version_control", "project_management"]:
                # Specific departments use these
                users = [e for e in self.employees if e["department"] in ["Engineering", "Product", "Data & Analytics"]]
            else:
                # Random subset
                users = random.sample(self.employees, min(system["users_count"], len(self.employees)))
            
            for user in users:
                self.relationships["system_usage"].append({
                    "from": user["name"],
                    "to": system["name"],
                    "type": "USES",
                    "usage_frequency": random.choice(["daily", "daily", "weekly", "monthly"]),
                    "proficiency": random.choice(["beginner", "intermediate", "intermediate", "expert"])
                })
        
        # Process ownership and participation
        for process in self.processes:
            # Owner relationship
            self.relationships["process_ownership"].append({
                "from": process["owner"],
                "to": process["name"],
                "type": "OWNS",
                "ownership_type": "primary",
                "responsibility_level": "full"
            })
            
            # Participants
            dept_employees = [e for e in self.employees if e["department"] == process["department"]]
            participants = random.sample(dept_employees, min(process["participants_count"], len(dept_employees)))
            
            for participant in participants:
                if participant["name"] != process["owner"]:
                    self.relationships["collaboration"].append({
                        "from": participant["name"],
                        "to": process["name"],
                        "type": "PERFORMS",
                        "role": random.choice(["participant", "reviewer", "approver"]),
                        "frequency": process["frequency"]
                    })
        
        return self.relationships
    
    def generate_slack_interactions(self, num_messages: int = 1000) -> List[Dict[str, Any]]:
        """Generate mock Slack message metadata."""
        if not self.employees:
            self.generate_employees()
        
        channels = [
            "#general", "#engineering", "#product", "#sales", "#marketing",
            "#customer-success", "#random", "#announcements", "#hr",
            "#data-analytics", "#design", "#operations"
        ]
        
        for _ in range(num_messages):
            sender = random.choice(self.employees)
            timestamp = datetime.now() - timedelta(days=random.randint(0, 90), 
                                                   hours=random.randint(0, 23),
                                                   minutes=random.randint(0, 59))
            
            message = {
                "sender_id": sender["email"],
                "sender_name": sender["name"],
                "channel": random.choice(channels),
                "timestamp": timestamp.isoformat(),
                "message_length": random.randint(10, 500),
                "has_thread": random.random() > 0.7,
                "thread_depth": random.randint(1, 15) if random.random() > 0.7 else 0,
                "reactions_count": random.randint(0, 10),
                "mentions": random.sample([e["email"] for e in self.employees], 
                                        random.randint(0, min(3, len(self.employees)))),
                "has_attachment": random.random() > 0.8
            }
            self.slack_messages.append(message)
        
        return self.slack_messages
    
    def generate_email_interactions(self, num_emails: int = 500) -> List[Dict[str, Any]]:
        """Generate mock email metadata."""
        if not self.employees:
            self.generate_employees()
        
        for _ in range(num_emails):
            sender = random.choice(self.employees)
            num_recipients = random.choices([1, 2, 3, 4, 5], weights=[40, 30, 15, 10, 5])[0]
            recipients = random.sample([e for e in self.employees if e != sender], 
                                      min(num_recipients, len(self.employees) - 1))
            
            email = {
                "sender": sender["email"],
                "recipients": [r["email"] for r in recipients],
                "cc_count": random.randint(0, 3),
                "timestamp": (datetime.now() - timedelta(days=random.randint(0, 90),
                                                        hours=random.randint(0, 23))).isoformat(),
                "subject_category": random.choice(["project_update", "meeting_request", "question", 
                                                   "approval", "announcement", "collaboration"]),
                "thread_length": random.randint(1, 8),
                "has_attachment": random.random() > 0.6,
                "response_latency_hours": random.choice([0.5, 1, 2, 4, 8, 24, 48])
            }
            self.emails.append(email)
        
        return self.emails
    
    def generate_calendar_events(self, num_events: int = 300) -> List[Dict[str, Any]]:
        """Generate mock calendar event data."""
        if not self.employees:
            self.generate_employees()
        
        meeting_types = [
            {"type": "1-1", "duration": 30, "participants": 2},
            {"type": "Team Sync", "duration": 60, "participants": (5, 10)},
            {"type": "All-Hands", "duration": 60, "participants": (20, 100)},
            {"type": "Project Review", "duration": 45, "participants": (4, 8)},
            {"type": "Interview", "duration": 60, "participants": (2, 4)},
            {"type": "Training", "duration": 120, "participants": (10, 30)}
        ]
        
        for _ in range(num_events):
            meeting_template = random.choice(meeting_types)
            participants_count = meeting_template["participants"] if isinstance(meeting_template["participants"], int) else random.randint(*meeting_template["participants"])
            
            event = {
                "title_category": meeting_template["type"],
                "organizer": random.choice(self.employees)["email"],
                "participants": [e["email"] for e in random.sample(self.employees, min(participants_count, len(self.employees)))],
                "participants_count": participants_count,
                "duration_minutes": meeting_template["duration"],
                "timestamp": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                "is_recurring": random.random() > 0.6,
                "recurrence_type": random.choice(["daily", "weekly", "bi-weekly", "monthly"]) if random.random() > 0.6 else None,
                "cross_department": random.random() > 0.5
            }
            self.calendar_events.append(event)
        
        return self.calendar_events
    
    def save_to_files(self, output_dir: Optional[str] = None) -> Dict[str, str]:
        """
        Save all generated data to JSON files.
        
        Args:
            output_dir: Directory to save files (default: data/ in project root)
        
        Returns:
            Dictionary mapping data types to file paths
        """
        output_path: Path
        if output_dir is None:
            # Default to data/ directory in project root
            project_root = Path(__file__).parent.parent.parent
            output_path = project_root / "data"
        else:
            output_path = Path(output_dir)
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamp and clean company name for filenames
        # Format: CompanyName_Type_YYYY-MM-DD_HHMMSS.json
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        # Clean company name: replace spaces with underscores, keep capitalization
        company_clean = self.company_name.replace(" ", "_").replace("/", "-").replace("\\", "-")
        
        file_paths = {}
        
        # Save entity data
        entities_data = {
            "company_name": self.company_name,
            "company_size": self.company_size,
            "generated_at": datetime.now().isoformat(),
            "employees": self.employees,
            "departments": self.departments,
            "projects": self.projects,
            "systems": self.systems,
            "processes": self.processes
        }
        
        entities_file = output_path / f"{company_clean}_Entities_{timestamp}.json"
        with open(entities_file, 'w') as f:
            json.dump(entities_data, f, indent=2)
        file_paths["entities"] = str(entities_file)
        
        # Save relationships data
        relationships_file = output_path / f"{company_clean}_Relationships_{timestamp}.json"
        with open(relationships_file, 'w') as f:
            json.dump(self.relationships, f, indent=2)
        file_paths["relationships"] = str(relationships_file)
        
        # Save communication data (Slack, Email, Calendar)
        communication_data = {
            "company_name": self.company_name,
            "generated_at": datetime.now().isoformat(),
            "slack_messages": self.slack_messages,
            "emails": self.emails,
            "calendar_events": self.calendar_events
        }
        
        communication_file = output_path / f"{company_clean}_Communications_{timestamp}.json"
        with open(communication_file, 'w') as f:
            json.dump(communication_data, f, indent=2)
        file_paths["communications"] = str(communication_file)
        
        # Save summary
        summary = {
            "company_name": self.company_name,
            "company_size": self.company_size,
            "generated_at": datetime.now().isoformat(),
            "statistics": {
                "total_employees": len(self.employees),
                "total_departments": len(self.departments),
                "total_projects": len(self.projects),
                "total_systems": len(self.systems),
                "total_processes": len(self.processes),
                "total_relationships": sum(len(v) for v in self.relationships.values()),
                "slack_messages": len(self.slack_messages),
                "emails": len(self.emails),
                "calendar_events": len(self.calendar_events)
            },
            "files_generated": file_paths
        }
        
        summary_file = output_path / f"{company_clean}_Summary_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        file_paths["summary"] = str(summary_file)
        
        return file_paths
    
    def generate_all(self) -> Dict[str, Any]:
        """Generate all organizational data."""
        print(f"Generating organizational data for {self.company_name} ({self.company_size})...")
        
        self.generate_departments()
        print(f"✓ Generated {len(self.departments)} departments")
        
        self.generate_employees()
        print(f"✓ Generated {len(self.employees)} employees")
        
        self.generate_projects()
        print(f"✓ Generated {len(self.projects)} projects")
        
        self.generate_systems()
        print(f"✓ Generated {len(self.systems)} systems")
        
        self.generate_processes()
        print(f"✓ Generated {len(self.processes)} processes")
        
        self.generate_relationships()
        total_relationships = sum(len(v) for v in self.relationships.values())
        print(f"✓ Generated {total_relationships} relationships")
        
        # Generate communication data (scaled to company size)
        messages_scale = {"small": 500, "medium": 1000, "large": 2000}
        email_scale = {"small": 250, "medium": 500, "large": 1000}
        event_scale = {"small": 150, "medium": 300, "large": 600}
        
        self.generate_slack_interactions(messages_scale[self.company_size])
        print(f"✓ Generated {len(self.slack_messages)} Slack messages")
        
        self.generate_email_interactions(email_scale[self.company_size])
        print(f"✓ Generated {len(self.emails)} emails")
        
        self.generate_calendar_events(event_scale[self.company_size])
        print(f"✓ Generated {len(self.calendar_events)} calendar events")
        
        return {
            "employees": self.employees,
            "departments": self.departments,
            "projects": self.projects,
            "systems": self.systems,
            "processes": self.processes,
            "relationships": self.relationships,
            "communications": {
                "slack_messages": self.slack_messages,
                "emails": self.emails,
                "calendar_events": self.calendar_events
            }
        }


def generate_mock_data(company_name: str, company_size: str = "medium", output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Main function to generate mock organizational data.
    
    Args:
        company_name: Name of the company
        company_size: Size of company (small, medium, large)
        output_dir: Directory to save output files
    
    Returns:
        Dictionary containing all generated data and file paths
    """
    generator = OrganizationalDataGenerator(company_name, company_size)
    data = generator.generate_all()
    file_paths = generator.save_to_files(output_dir)
    
    return {
        "success": True,
        "data": data,
        "files": file_paths,
        "statistics": {
            "total_employees": len(data["employees"]),
            "total_departments": len(data["departments"]),
            "total_projects": len(data["projects"]),
            "total_systems": len(data["systems"]),
            "total_processes": len(data["processes"]),
            "total_relationships": sum(len(v) for v in data["relationships"].values()),
            "total_communications": (
                len(data["communications"]["slack_messages"]) +
                len(data["communications"]["emails"]) +
                len(data["communications"]["calendar_events"])
            )
        }
    }


if __name__ == "__main__":
    # Example usage
    result = generate_mock_data("Acme Corporation", "medium")
    print("\n" + "="*50)
    print("Data generation complete!")
    print("="*50)
    print(f"\nFiles saved:")
    for data_type, file_path in result["files"].items():
        print(f"  - {data_type}: {file_path}")
    print(f"\nStatistics:")
    for key, value in result["statistics"].items():
        print(f"  - {key}: {value}")

