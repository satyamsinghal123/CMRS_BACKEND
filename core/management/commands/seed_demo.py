from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from core.models import Branch, BankAccount
from customers.models import Customer
from loans.models import Loan, RepaymentSchedule
from cashcollections.models import Repayment, AgentCashSubmission
from reconciliation.models import Reconciliation
from deposits.models import BankDeposit, Settlement

User = get_user_model()

class Command(BaseCommand):
    help = "Create CMRS demo data for local development."

    def handle(self, *args, **options):
        branch, _ = Branch.objects.get_or_create(
            code="NDL-01",
            defaults={"name": "North Delhi Branch", "address": "Delhi", "city": "Delhi"}
        )

        bank, _ = BankAccount.objects.get_or_create(
            branch=branch,
            bank_name="HDFC Bank",
            account_last4="0421",
            defaults={"account_holder": "CMRS Collections"}
        )

        def user(username, email, password, role, employee_code):
            obj, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "role": role,
                    "employee_code": employee_code,
                    "first_name": username.split(".")[0].title(),
                    "last_name": "User",
                }
            )
            obj.role = role
            obj.employee_code = employee_code
            obj.set_password(password)
            obj.save()
            return obj

        admin = user("admin", "admin@cmrs.local", "Admin@12345", "ADMIN", "ADM001")
        manager = user("manager", "manager@cmrs.local", "Manager@12345", "BRANCH_MANAGER", "MGR001")
        agent1 = user("vikas", "vikas@cmrs.local", "Agent@12345", "COLLECTION_AGENT", "AGT001")
        agent2 = user("priya", "priya@cmrs.local", "Agent@12345", "COLLECTION_AGENT", "AGT002")
        agent3 = user("rakesh", "rakesh@cmrs.local", "Agent@12345", "COLLECTION_AGENT", "AGT003")

        demo_customers = [
            ("CUS-100482", "Rahul Mehta", "9811122146", agent1, "LN-104892", Decimal("250000"), Decimal("184500"), Decimal("12500")),
            ("CUS-100431", "Neha Gupta", "9711165020", agent2, "LN-104731", Decimal("150000"), Decimal("96750"), Decimal("8750")),
            ("CUS-100398", "Amit Verma", "9911101077", agent1, "LN-104588", Decimal("300000"), Decimal("242000"), Decimal("10000")),
            ("CUS-100341", "Sunita Devi", "8811133321", agent2, "LN-104401", Decimal("100000"), Decimal("68200"), Decimal("15000")),
            ("CUS-100290", "Mohit Bansal", "9811198877", agent2, "LN-104290", Decimal("200000"), Decimal("120000"), Decimal("7500")),
        ]

        for cid, name, phone, agent, loan_id, principal, outstanding, monthly in demo_customers:
            customer, _ = Customer.objects.get_or_create(
                customer_id=cid,
                defaults={"full_name": name, "phone": phone, "branch": branch, "assigned_agent": agent}
            )
            customer.full_name = name
            customer.phone = phone
            customer.branch = branch
            customer.assigned_agent = agent
            customer.save()

            loan, _ = Loan.objects.get_or_create(
                loan_id=loan_id,
                defaults={
                    "customer": customer, "branch": branch, "principal_amount": principal,
                    "outstanding_amount": outstanding, "monthly_due": monthly,
                    "interest_rate": Decimal("12.500"), "start_date": timezone.localdate() - timedelta(days=180)
                }
            )

            Loan.objects.filter(pk=loan.pk).update(
                customer=customer, branch=branch, principal_amount=principal,
                outstanding_amount=outstanding, monthly_due=monthly
            )

            schedule, _ = RepaymentSchedule.objects.get_or_create(
                loan=loan,
                installment_number=1,
                defaults={
                    "due_date": timezone.localdate(),
                    "expected_amount": monthly,
                    "paid_amount": Decimal("0.00")
                }
            )
            RepaymentSchedule.objects.filter(pk=schedule.pk).update(
                due_date=timezone.localdate(),
                expected_amount=monthly,
            )

        # Seed a few repayments, submissions and reconciliations if empty.
        if not Repayment.objects.exists():
            loan1 = Loan.objects.get(loan_id="LN-104892")
            loan2 = Loan.objects.get(loan_id="LN-104731")
            loan3 = Loan.objects.get(loan_id="LN-104588")
            Repayment.objects.create(
                receipt_number="RC-20261008-0184", customer=loan1.customer, loan=loan1,
                schedule=loan1.schedule.first(), agent=agent1, branch=branch,
                amount=Decimal("12500"), expected_amount=Decimal("12500"),
                payment_type="FULL", collection_date=timezone.localdate()
            )
            Repayment.objects.create(
                receipt_number="RC-20261008-0183", customer=loan2.customer, loan=loan2,
                schedule=loan2.schedule.first(), agent=agent2, branch=branch,
                amount=Decimal("8750"), expected_amount=Decimal("8750"),
                payment_type="FULL", collection_date=timezone.localdate()
            )
            Repayment.objects.create(
                receipt_number="RC-20261008-0182", customer=loan3.customer, loan=loan3,
                schedule=loan3.schedule.first(), agent=agent1, branch=branch,
                amount=Decimal("5000"), expected_amount=Decimal("10000"),
                payment_type="PARTIAL", collection_date=timezone.localdate()
            )
        Repayment.objects.filter(receipt_number__startswith="RC-20261008-").update(
            collection_date=timezone.localdate()
        )

        if not AgentCashSubmission.objects.exists():
            submissions = [
                ("SUB-20261008-044", agent1, Decimal("42500"), Decimal("42500"), "APPROVED"),
                ("SUB-20261008-043", agent3, Decimal("31500"), Decimal("30000"), "PENDING"),
                ("SUB-20261008-042", agent2, Decimal("38250"), Decimal("38250"), "APPROVED"),
                ("SUB-20261008-041", agent2, Decimal("27750"), Decimal("26000"), "PENDING"),
            ]
            for number, agent, expected, received, status in submissions:
                AgentCashSubmission.objects.create(
                    submission_number=number, agent=agent, branch=branch,
                    expected_amount=expected, received_amount=received, status=status
                )
        AgentCashSubmission.objects.filter(submission_number__startswith="SUB-20261008-").update(
            submission_date=timezone.localdate()
        )

        if not Reconciliation.objects.exists():
            for sub in AgentCashSubmission.objects.all():
                Reconciliation.objects.create(
                    submission=sub, branch=branch,
                    expected_amount=sub.expected_amount,
                    received_amount=sub.received_amount,
                    status="APPROVED" if sub.status == "APPROVED" else "PENDING",
                    reviewed_by=manager if sub.status == "APPROVED" else None
                )

        if not BankDeposit.objects.exists():
            approved = Reconciliation.objects.filter(status="APPROVED").first()
            if approved:
                deposit = BankDeposit.objects.create(
                    deposit_number="DEP-20261008-001",
                    branch=branch,
                    reconciliation=approved,
                    bank_account=bank,
                    amount=approved.received_amount,
                    deposit_date=timezone.localdate(),
                    bank_reference="HDFC-884201",
                    created_by=manager,
                    status="SETTLED",
                )
                Settlement.objects.create(
                    deposit=deposit,
                    settled_amount=deposit.amount,
                    settlement_date=timezone.now(),
                    settlement_reference="SET-884201",
                    status="SETTLED"
                )
        demo_deposit = BankDeposit.objects.filter(deposit_number="DEP-20261008-001").first()
        if demo_deposit:
            BankDeposit.objects.filter(pk=demo_deposit.pk).update(deposit_date=timezone.localdate())
            Settlement.objects.filter(deposit=demo_deposit).update(
                settlement_date=timezone.now(), settled_amount=demo_deposit.amount, status="SETTLED"
            )

        self.stdout.write(self.style.SUCCESS("CMRS demo data created/updated."))
        self.stdout.write("Admin: admin / Admin@12345")
        self.stdout.write("Manager: manager / Manager@12345")
        self.stdout.write("Agent: vikas / Agent@12345")
