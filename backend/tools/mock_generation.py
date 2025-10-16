"""
Mock data generation tool for organizational intelligence.

This module generates realistic mock data for organizational entities and relationships
with proper ratios and connectivity. The generated data can be used by agents to create 
Neo4j nodes and relationships.
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
    """Generates realistic mock organizational data with proper ratios and connectivity."""
    
    def __init__(self, company_name: str, company_size: str = "medium"):
        """
        Initialize the data generator.
        
        Args:
            company_name: Name of the company
            company_size: Size of company (small: 5, medium: 15, large: 30)
        """
        self.company_name = company_name
        self.company_size = company_size
        
        if FAKER_AVAILABLE:
            self.fake = Faker()
        else:
            self.fake = None
        
        # Define company size parameters with new ratios
        # Ratios: 1 Employee:3 Processes, 1 Department:3 Employees, 1 Project:3 Employees
        self.size_params = {
            "small": {
                "employees": 5,
                "departments": 2,  # 5 employees / 3 = ~2 departments
                "projects": 2,     # 5 employees / 3 = ~2 projects
                "processes": 15,   # 5 employees * 3 = 15 processes
                "systems": 3       # Reduced systems for smaller companies
            },
            "medium": {
                "employees": 15,
                "departments": 5,  # 15 employees / 3 = 5 departments
                "projects": 5,     # 15 employees / 3 = 5 projects
                "processes": 45,   # 15 employees * 3 = 45 processes
                "systems": 8       # Moderate systems for medium companies
            },
            "large": {
                "employees": 30,
                "departments": 10, # 30 employees / 3 = 10 departments
                "projects": 10,    # 30 employees / 3 = 10 projects
                "processes": 90,   # 30 employees * 3 = 90 processes
                "systems": 15      # More systems for large companies
            }
        }
        
        self.params = self.size_params.get(company_size, self.size_params["medium"])
        
        # Data storage - only entities and relationships
        self.employees = []
        self.departments = []
        self.projects = []
        self.systems = []
        self.processes = []
        
        # Relationship storage - focused on organizational structure
        self.relationships = {
            "reports_to": [],        # Employee hierarchy
            "works_with": [],        # Employee collaboration
            "belongs_to_department": [],  # Employee-department relationships
            "assigned_to_project": [],    # Employee-project relationships
            "owns_process": [],      # Employee-process ownership
            "uses_system": [],       # Employee-system usage
            "process_belongs_to_project": []  # Process-project relationships
        }
    
    def _generate_name(self) -> str:
        """Generate a realistic person name."""
        if self.fake:
            return self.fake.name()
        else:
            first_names = ["Alice", "Bob", "Carol", "David", "Emma", "Frank", "Grace", "Henry", 
                          "Isabel", "Jack", "Kate", "Leo", "Maria", "Nathan", "Olivia", "Peter",
                          "Quinn", "Rachel", "Sam", "Tina", "Uma", "Victor", "Wendy", "Xavier", "Yara", "Zoe"]
            last_names = ["Anderson", "Brown", "Clark", "Davis", "Evans", "Foster", "Garcia", "Harris",
                         "Johnson", "King", "Lee", "Miller", "Nelson", "O'Connor", "Parker", "Quinn",
                         "Roberts", "Smith", "Taylor", "Upton", "Vargas", "White", "Young", "Zhang"]
            return f"{random.choice(first_names)} {random.choice(last_names)}"
    
    def _generate_email(self, name: str) -> str:
        """Generate email from name."""
        if self.fake:
            return self.fake.email()
        else:
            # Simple email generation
            first, last = name.lower().split(' ', 1)
            domains = ["company.com", "techcorp.com", "innovate.io", "future.com"]
            return f"{first}.{last}@{random.choice(domains)}"
    
    def _generate_skills(self, department: str) -> List[str]:
        """Generate relevant skills for department."""
        skill_sets = {
            "Engineering": ["Python", "JavaScript", "React", "Node.js", "AWS", "Docker", "Kubernetes", "Git", "Testing", "Architecture"],
            "Product": ["Product Management", "User Research", "Analytics", "Figma", "Jira", "A/B Testing", "Strategy", "Roadmapping"],
            "Sales": ["CRM", "Lead Generation", "Negotiation", "Salesforce", "HubSpot", "Cold Calling", "Relationship Building", "Closing"],
            "Marketing": ["SEO", "SEM", "Content Marketing", "Social Media", "Analytics", "Campaign Management", "Branding", "Growth"],
            "Customer Success": ["Customer Support", "Account Management", "Zendesk", "Intercom", "Retention", "Onboarding", "Training"],
            "Finance": ["Financial Analysis", "Excel", "QuickBooks", "Budgeting", "Forecasting", "Compliance", "Reporting", "Modeling"],
            "HR": ["Recruiting", "Employee Relations", "Performance Management", "Benefits", "Training", "Culture", "Compliance"],
            "Operations": ["Process Improvement", "Vendor Management", "IT Administration", "Compliance", "Project Management", "Quality"],
            "Legal": ["Contract Law", "Compliance", "Risk Management", "Intellectual Property", "Regulatory", "Negotiation", "Research"],
            "Data & Analytics": ["SQL", "Python", "Tableau", "Machine Learning", "Statistics", "Data Visualization", "ETL", "Modeling"]
        }
        available_skills = skill_sets.get(department, ["Communication", "Problem Solving", "Leadership", "Teamwork", "Adaptability"])
        num_skills = min(random.randint(3, 6), len(available_skills))
        return random.sample(available_skills, num_skills)
    
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
        
        # Calculate employees per department (1 Department: 3 Employees ratio)
        employees_per_dept = self.params["employees"] // num_depts
        remaining_employees = self.params["employees"] % num_depts
        
        for i, dept_template in enumerate(selected_depts):
            budget_min, budget_max = dept_template["budget_range"]
            # Distribute remaining employees to first few departments
            dept_headcount = employees_per_dept + (1 if i < remaining_employees else 0)
            
            dept = {
                "name": dept_template["name"],
                "description": f"{dept_template['name']} department responsible for {', '.join(dept_template['functions'])}",
                "budget": random.randint(budget_min, budget_max),
                "headcount": dept_headcount,
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
                    "level": random.choice(["Junior", "Mid-level", "Senior", "Staff"]),
                    "tenure_years": random.uniform(0.5, 8),
                    "salary": random.randint(60000, 180000),
                    "location": dept["location"],
                    "skills": self._generate_skills(dept_name),
                    "status": "active",
                    "start_date": (datetime.now() - timedelta(days=random.randint(30, 2920))).isoformat()
                }
                self.employees.append(employee)
        
        return self.employees
    
    def generate_projects(self) -> List[Dict[str, Any]]:
        """Generate project data."""
        if not self.departments:
            self.generate_departments()
        
        project_templates = [
            {"name": "Digital Transformation", "type": "strategic", "duration_months": 12},
            {"name": "Customer Experience Enhancement", "type": "product", "duration_months": 8},
            {"name": "Data Analytics Platform", "type": "technical", "duration_months": 6},
            {"name": "Sales Process Optimization", "type": "operational", "duration_months": 4},
            {"name": "Security Infrastructure Upgrade", "type": "technical", "duration_months": 10},
            {"name": "Market Expansion Initiative", "type": "strategic", "duration_months": 18},
            {"name": "Product Feature Development", "type": "product", "duration_months": 3},
            {"name": "Employee Engagement Program", "type": "operational", "duration_months": 6},
            {"name": "Compliance Framework Implementation", "type": "regulatory", "duration_months": 9},
            {"name": "Performance Optimization", "type": "technical", "duration_months": 5}
        ]
        
        num_projects = self.params["projects"]
        selected_projects = random.sample(project_templates, min(num_projects, len(project_templates)))
        
        for i, project_template in enumerate(selected_projects):
            # Distribute projects across departments
            dept = self.departments[i % len(self.departments)]
            
            project = {
                "name": project_template["name"],
                "description": f"{project_template['name']} project for {dept['name']} department",
                "type": project_template["type"],
                "department": dept["name"],
                "status": random.choice(["planning", "active", "active", "active", "completed"]),
                "priority": random.choice(["low", "medium", "high", "critical"]),
                "budget": random.randint(50000, 500000),
                "start_date": (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat(),
                "end_date": (datetime.now() + timedelta(days=random.randint(90, 540))).isoformat(),
                "duration_months": project_template["duration_months"],
                "team_size": 3  # 1 Project: 3 Employees ratio
            }
            self.projects.append(project)
        
        return self.projects
    
    def generate_systems(self) -> List[Dict[str, Any]]:
        """Generate system/technology data."""
        system_templates = [
            {"name": "Slack", "type": "communication", "users_count": 50},
            {"name": "Microsoft Teams", "type": "communication", "users_count": 30},
            {"name": "Salesforce", "type": "crm", "users_count": 20},
            {"name": "HubSpot", "type": "marketing", "users_count": 15},
            {"name": "Jira", "type": "project_management", "users_count": 25},
            {"name": "Confluence", "type": "documentation", "users_count": 40},
            {"name": "GitHub", "type": "version_control", "users_count": 20},
            {"name": "AWS", "type": "cloud_infrastructure", "users_count": 10},
            {"name": "Google Workspace", "type": "productivity", "users_count": 50},
            {"name": "Zoom", "type": "video_conferencing", "users_count": 45},
            {"name": "Tableau", "type": "analytics", "users_count": 8},
            {"name": "ServiceNow", "type": "it_service_management", "users_count": 12}
        ]
        
        num_systems = self.params["systems"]
        selected_systems = random.sample(system_templates, min(num_systems, len(system_templates)))
        
        for system_template in selected_systems:
            system = {
                "name": system_template["name"],
                "type": system_template["type"],
                "description": f"{system_template['name']} system for organizational operations",
                "vendor": random.choice(["Microsoft", "Google", "Salesforce", "Atlassian", "Amazon", "Oracle"]),
                "users_count": system_template["users_count"],
                "status": "active",
                "cost_annual": random.randint(5000, 200000),
                "implementation_date": (datetime.now() - timedelta(days=random.randint(365, 1825))).isoformat()
            }
            self.systems.append(system)
        
        return self.systems
    
    def generate_processes(self) -> List[Dict[str, Any]]:
        """Generate business process data with 1 Employee: 3 Processes ratio."""
        if not self.departments:
            self.generate_departments()
        if not self.employees:
            self.generate_employees()
        
        process_templates = {
            "Engineering": ["Code Review", "Sprint Planning", "Deployment", "Incident Response", "Technical Design Review", "Testing", "Documentation", "Architecture Review"],
            "Product": ["Product Discovery", "User Research", "Feature Prioritization", "Release Planning", "Stakeholder Alignment", "Market Analysis"],
            "Sales": ["Lead Qualification", "Demo Scheduling", "Contract Negotiation", "Deal Review", "Pipeline Management", "Customer Outreach"],
            "Marketing": ["Content Approval", "Campaign Planning", "Lead Scoring", "Event Management", "Brand Review", "Analytics Review"],
            "Customer Success": ["Customer Onboarding", "Ticket Escalation", "QBR Preparation", "Renewal Process", "Health Check", "Training"],
            "Finance": ["Invoice Processing", "Expense Approval", "Budget Review", "Month-End Close", "Financial Planning", "Audit Preparation"],
            "HR": ["Candidate Screening", "Offer Approval", "Performance Review", "Employee Onboarding", "Training Coordination", "Policy Review"],
            "Operations": ["Vendor Approval", "Access Provisioning", "Asset Management", "Compliance Check", "Security Review", "Process Optimization"],
        }
        
        # Generate the target number of processes (1 Employee: 3 Processes)
        target_processes = self.params["processes"]
        processes_generated = 0
        
        # Generate processes for each department
        for dept in self.departments:
            dept_name = dept["name"]
            dept_processes = process_templates.get(dept_name, ["Standard Process", "Review Process", "Approval Process", "Monitoring Process"])
            
            # Calculate processes for this department
            dept_employees = [e for e in self.employees if e["department"] == dept_name]
            dept_process_count = len(dept_employees) * 3  # 3 processes per employee
            
            for i in range(dept_process_count):
                if processes_generated >= target_processes:
                    break
                    
                proc_name = dept_processes[i % len(dept_processes)]
                if i >= len(dept_processes):
                    proc_name = f"Process {i + 1}"
                
                # Select owner from department employees
                owner = random.choice(dept_employees) if dept_employees else self.employees[0]
                
                process = {
                    "name": proc_name,
                    "description": f"{proc_name} process for {dept_name} department",
                    "category": dept_name,
                    "owner": owner["name"],
                    "department": dept_name,
                    "frequency": random.choice(["daily", "weekly", "monthly", "quarterly", "as-needed"]),
                    "complexity": random.choice(["low", "medium", "medium", "high"]),
                    "automation_level": random.choice(["manual", "semi-automated", "automated"]),
                    "sla_hours": random.choice([2, 4, 8, 24, 48, 72]),
                    "status": "active",
                    "participants_count": random.randint(2, 10),
                    "created_date": (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat()
                }
                self.processes.append(process)
                processes_generated += 1
        
        return self.processes
    
    def generate_relationships(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generate relationship data between entities with proper connectivity."""
        if not self.employees:
            self.generate_employees()
        if not self.projects:
            self.generate_projects()
        if not self.systems:
            self.generate_systems()
        if not self.processes:
            self.generate_processes()
        
        # 1. Create organizational hierarchy (Reports_To relationships)
        self._create_reports_to_hierarchy()
        
        # 2. Create employee collaboration network (Works_With relationships)
        self._create_works_with_network()
        
        # 3. Department membership (1 Department: 3 Employees ratio)
        self._create_department_memberships()
        
        # 4. Project assignments (1 Project: 3 Employees ratio)
        self._create_project_assignments()
        
        # 5. Process ownership (1 Employee: 3 Processes ratio)
        self._create_process_ownerships()
        
        # 6. System usage
        self._create_system_usage()
        
        # 7. Process-project relationships
        self._create_process_project_relationships()
        
        # 8. Clean up any duplicate relationships
        self._cleanup_duplicate_relationships()
        
        return self.relationships
    
    def _create_reports_to_hierarchy(self):
        """Create Reports_To relationships ensuring all employees are connected."""
        # Create a hierarchical structure
        # 1. Identify managers (top 20% by seniority/level)
        managers = sorted(self.employees, key=lambda x: x.get('level', 1), reverse=True)[:max(1, len(self.employees) // 5)]
        
        # 2. Create CEO/executive level
        if managers:
            ceo = managers[0]
            ceo['is_ceo'] = True
            
            # All other managers report to CEO
            for manager in managers[1:]:
                self.relationships["reports_to"].append({
                    "from": manager["name"],
                    "to": ceo["name"],
                    "type": "REPORTS_TO",
                    "relationship_type": "direct_report",
                    "start_date": manager["start_date"]
                })
        
        # 3. Assign remaining employees to managers
        non_managers = [emp for emp in self.employees if emp not in managers]
        
        for employee in non_managers:
            # Assign to a random manager
            manager = random.choice(managers)
            self.relationships["reports_to"].append({
                "from": employee["name"],
                "to": manager["name"],
                "type": "REPORTS_TO",
                "relationship_type": "direct_report",
                "start_date": employee["start_date"]
            })
    
    def _create_works_with_network(self):
        """Create Works_With relationships ensuring all employees are connected, avoiding conflicts with REPORTS_TO."""
        # Create a connected network where every employee works with at least 2-3 others
        
        # First, get existing REPORTS_TO relationships to avoid conflicts
        existing_reports_to = set()
        for rel in self.relationships.get("reports_to", []):
            # Add both directions to avoid conflicts
            existing_reports_to.add((rel["from"], rel["to"]))
            existing_reports_to.add((rel["to"], rel["from"]))
        
        # 1. Create department-based collaborations
        dept_groups = {}
        for emp in self.employees:
            dept = emp["department"]
            if dept not in dept_groups:
                dept_groups[dept] = []
            dept_groups[dept].append(emp)
        
        # 2. Within each department, create collaboration networks
        for dept, employees in dept_groups.items():
            if len(employees) > 1:
                # Create a connected graph within the department
                for i, emp1 in enumerate(employees):
                    # Each employee works with 2-3 others in their department
                    # Filter out employees who already have REPORTS_TO relationships
                    available_collaborators = [
                        e for j, e in enumerate(employees) 
                        if j != i and (emp1["name"], e["name"]) not in existing_reports_to
                    ]
                    
                    # Select 2-3 collaborators from available ones
                    num_collaborators = min(3, len(available_collaborators))
                    if num_collaborators > 0:
                        collaborators = random.sample(available_collaborators, num_collaborators)
                        
                        for emp2 in collaborators:
                            self.relationships["works_with"].append({
                                "from": emp1["name"],
                                "to": emp2["name"],
                                "type": "WORKS_WITH",
                                "collaboration_type": "peer",
                                "frequency": random.choice(["daily", "weekly", "weekly", "monthly"]),
                                "context": f"Department: {dept}"
                            })
        
        # 3. Create cross-department collaborations
        all_employees = self.employees.copy()
        for emp in all_employees:
            # Each employee works with 1-2 people from other departments
            # Filter out employees who already have REPORTS_TO relationships
            other_dept_employees = [
                e for e in all_employees 
                if e["department"] != emp["department"] 
                and (emp["name"], e["name"]) not in existing_reports_to
            ]
            
            if other_dept_employees:
                num_collaborators = min(2, len(other_dept_employees))
                cross_dept_collaborators = random.sample(other_dept_employees, num_collaborators)
                
                for collaborator in cross_dept_collaborators:
                    self.relationships["works_with"].append({
                        "from": emp["name"],
                        "to": collaborator["name"],
                        "type": "WORKS_WITH",
                        "collaboration_type": "cross_department",
                        "frequency": random.choice(["weekly", "monthly", "monthly"]),
                        "context": f"Cross-department collaboration"
                    })
    
    def _cleanup_duplicate_relationships(self):
        """Remove duplicate relationships and ensure no conflicts between REPORTS_TO and WORKS_WITH."""
        # Get all REPORTS_TO relationships
        reports_to_pairs = set()
        for rel in self.relationships.get("reports_to", []):
            reports_to_pairs.add((rel["from"], rel["to"]))
            reports_to_pairs.add((rel["to"], rel["from"]))  # Add both directions
        
        # Filter out WORKS_WITH relationships that conflict with REPORTS_TO
        filtered_works_with = []
        for rel in self.relationships.get("works_with", []):
            pair = (rel["from"], rel["to"])
            if pair not in reports_to_pairs:
                filtered_works_with.append(rel)
            else:
                print(f"Removing conflicting WORKS_WITH relationship: {rel['from']} <-> {rel['to']} (already has REPORTS_TO)")
        
        self.relationships["works_with"] = filtered_works_with
        
        # Also remove any exact duplicates within each relationship type
        for rel_type in self.relationships:
            seen = set()
            unique_rels = []
            for rel in self.relationships[rel_type]:
                # Create a unique key for the relationship
                key = (rel["from"], rel["to"], rel["type"])
                if key not in seen:
                    seen.add(key)
                    unique_rels.append(rel)
                else:
                    print(f"Removing duplicate {rel_type} relationship: {rel['from']} -> {rel['to']}")
            self.relationships[rel_type] = unique_rels
    
    def _create_department_memberships(self):
        """Create department memberships with 1 Department: 3 Employees ratio."""
        # Distribute employees evenly across departments
        employees_per_dept = len(self.employees) // len(self.departments)
        remaining_employees = len(self.employees) % len(self.departments)
        
        employee_index = 0
        for i, dept in enumerate(self.departments):
            # Calculate how many employees for this department
            dept_size = employees_per_dept + (1 if i < remaining_employees else 0)
            
            # Assign employees to this department
            for j in range(dept_size):
                if employee_index < len(self.employees):
                    emp = self.employees[employee_index]
                    emp["department"] = dept["name"]  # Update employee's department
                    
                    self.relationships["belongs_to_department"].append({
                        "from": emp["name"],
                        "to": dept["name"],
                        "type": "BELONGS_TO",
                        "allocation_percentage": 100,
                        "start_date": emp["start_date"]
                    })
                    employee_index += 1
    
    def _create_project_assignments(self):
        """Create project assignments with 1 Project: 3 Employees ratio."""
        # Distribute employees evenly across projects
        employees_per_project = len(self.employees) // len(self.projects)
        remaining_employees = len(self.employees) % len(self.projects)
        
        employee_index = 0
        for i, project in enumerate(self.projects):
            # Calculate how many employees for this project
            project_size = employees_per_project + (1 if i < remaining_employees else 0)
            
            # Assign employees to this project
            for j in range(project_size):
                if employee_index < len(self.employees):
                    emp = self.employees[employee_index]
                    
                    self.relationships["assigned_to_project"].append({
                        "from": emp["name"],
                        "to": project["name"],
                        "type": "ASSIGNED_TO",
                        "role": random.choice(["developer", "analyst", "coordinator", "reviewer"]),
                        "allocation_percentage": random.choice([100, 80, 50]),
                        "start_date": emp["start_date"]
                    })
                    employee_index += 1
    
    def _create_process_ownerships(self):
        """Create process ownerships with 1 Employee: 3 Processes ratio."""
        # Distribute processes evenly across employees
        processes_per_employee = len(self.processes) // len(self.employees)
        remaining_processes = len(self.processes) % len(self.employees)
        
        process_index = 0
        for i, emp in enumerate(self.employees):
            # Calculate how many processes for this employee
            emp_process_count = processes_per_employee + (1 if i < remaining_processes else 0)
            
            # Assign processes to this employee
            for j in range(emp_process_count):
                if process_index < len(self.processes):
                    process = self.processes[process_index]
                    process["owner"] = emp["name"]  # Update process owner
                    
                    self.relationships["owns_process"].append({
                        "from": emp["name"],
                        "to": process["name"],
                        "type": "OWNS",
                        "ownership_type": "primary",
                        "responsibility_level": "full"
                    })
                    process_index += 1
    
    def _create_system_usage(self):
        """Create system usage relationships."""
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
                self.relationships["uses_system"].append({
                    "from": user["name"],
                    "to": system["name"],
                    "type": "USES",
                    "usage_frequency": random.choice(["daily", "daily", "weekly", "monthly"]),
                    "proficiency": random.choice(["beginner", "intermediate", "intermediate", "expert"])
                })
    
    def _create_process_project_relationships(self):
        """Create relationships between processes and projects."""
        for process in self.processes:
            # Each process belongs to 1-2 projects
            assigned_projects = random.sample(self.projects, min(2, len(self.projects)))
            
            for project in assigned_projects:
                self.relationships["process_belongs_to_project"].append({
                    "from": process["name"],
                    "to": project["name"],
                    "type": "BELONGS_TO",
                    "relationship_type": "process_project",
                    "start_date": process["created_date"]
                })
    
    def save_to_files(self, output_dir: Optional[str] = None) -> Dict[str, str]:
        """Save generated data to JSON files."""
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Clear existing data files before saving new ones
        print(f"🧹 Clearing existing data files in {output_path}...")
        for file_path in output_path.glob("*.json"):
            try:
                file_path.unlink()
                print(f"   ✓ Deleted {file_path.name}")
            except Exception as e:
                print(f"   ⚠️  Could not delete {file_path.name}: {e}")
        
        print(f"✅ Data folder cleared, ready for new files")
        
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
                "total_relationships": sum(len(v) for v in self.relationships.values())
            },
            "files_generated": file_paths
        }
        
        summary_file = output_path / f"{company_clean}_Summary_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        file_paths["summary"] = str(summary_file)
        
        return file_paths
    
    def generate_all(self) -> Dict[str, Any]:
        """Generate all organizational data - entities and relationships only."""
        print(f"Generating organizational data for {self.company_name} ({self.company_size})...")
        print(f"Target ratios: 1 Employee:3 Processes, 1 Department:3 Employees, 1 Project:3 Employees")
        
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
        
        # Verify ratios
        print(f"\n📊 Generated Data Summary:")
        print(f"  - Employees: {len(self.employees)}")
        print(f"  - Departments: {len(self.departments)} (ratio: {len(self.employees)/len(self.departments):.1f} employees/dept)")
        print(f"  - Projects: {len(self.projects)} (ratio: {len(self.employees)/len(self.projects):.1f} employees/project)")
        print(f"  - Processes: {len(self.processes)} (ratio: {len(self.processes)/len(self.employees):.1f} processes/employee)")
        print(f"  - Systems: {len(self.systems)}")
        print(f"  - Total Relationships: {total_relationships}")
        
        return {
            "employees": self.employees,
            "departments": self.departments,
            "projects": self.projects,
            "systems": self.systems,
            "processes": self.processes,
            "relationships": self.relationships
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
            "total_relationships": sum(len(v) for v in data["relationships"].values())
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
