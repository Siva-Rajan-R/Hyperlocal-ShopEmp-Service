import os

file_path = r'D:\Projects\Hyperlocal-Inventory\Frontends\market-place\src\features\employee\pages\EmployeeVerifyPage.tsx'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_content = """        {verified && (
          <div className="rounded-lg bg-slate-50 border border-slate-100 p-4 text-left space-y-2">
            {employeeId && <p className="text-xs font-bold text-slate-500 break-all">Employee ID: {employeeId}</p>}
            {shopId && <p className="text-xs font-bold text-slate-500 break-all">Shop ID: {shopId}</p>}
          </div>
        )}"""

new_content = """        {verified && (
          <div className="rounded-lg bg-emerald-50/50 border border-emerald-100 p-4 text-center space-y-2">
            {shopName && <p className="text-sm font-bold text-slate-700">Shop: {shopName}</p>}
            <p className="text-sm font-medium text-slate-600">Your login credentials will be sent to your email shortly.</p>
          </div>
        )}"""

content = content.replace(
"""  const employeeId = params.get("employee_id");
  const shopId = params.get("shop_id");""",
"""  const shopName = params.get("shop_name");"""
)

content = content.replace(old_content, new_content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated frontend successfully')
