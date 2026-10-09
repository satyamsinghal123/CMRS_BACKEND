CMRS Collection Workflow Update

What changed
- Managers/admin/operations can assign customers to active collection agents from Customer Management.
- Collection agents can only see customers and repayments assigned/recorded to them through the relevant APIs.
- The Collection page displays due and overdue unpaid installments for the logged-in agent, including customer, loan, installment, due date, expected, paid, and remaining amounts.
- Record Payment from a task fills customer, loan, and schedule identifiers automatically; the agent enters the actual amount received.
- Backend validates that the customer belongs to the loan, that an agent is assigned to the customer, and that the schedule belongs to the loan.
- Partial payments update the schedule and reduce outstanding balance by the amount applied.
- Over-collections are recorded and classified; the schedule and loan balance only apply the amount still due, so the excess is not silently applied to the loan balance.
- Agents can record unsuccessful collection attempts with a reason and notes.

Install/update
1. Back up your existing PostgreSQL database first.
2. Copy your existing local .env into this backend folder (it is deliberately not included in the ZIP), or configure a new .env using .env.example.
3. Install Python dependencies if needed: pip install -r requirements.txt
4. Run: python manage.py migrate
5. Run: python manage.py check
6. Start backend: python manage.py runserver
7. In frontend folder run: npm install, then npm run dev.

Notes
- Existing customers already have an assigned_agent field; this update uses it rather than creating duplicate assignment records.
- Customers must have a branch, a loan, and a repayment schedule before a scheduled collection can be recorded.
- The current loan model has no detailed interest/fee allocation ledger. The balance logic applies the amount due against the schedule and outstanding loan amount; a production lending ledger should explicitly allocate principal, interest, fees, and excess funds.
- This ZIP does not contain .env or customer database data.
