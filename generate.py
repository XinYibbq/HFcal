from datetime import datetime, timedelta
from icalendar import Calendar, Event
import pytz

# ================= 配置区域 =================
# 1. 设置一个已知的"大周"的起始周一日期 (YYYY, M, D)
# 例如：2024年1月1日是周一，假设那天是大周开始
BASE_BIG_WEEK_START = datetime(2026, 2, 16) 

# 2. 日历基本信息
CALENDAR_NAME = "大小周工作提示"
CALENDAR_DESC = "自动计算大小周，大周显示'本周六上班'，小周显示'本周双休'"
TIMEZONE = 'Asia/Shanghai'

# 3. 生成范围 (前后各多少天，建议覆盖未来1-2年)
DAYS_RANGE = 800 
# ===========================================

def get_week_type(target_date):
    """
    判断目标日期所在周是'大周'还是'小周'
    返回: 'BIG' (大周/单休) 或 'SMALL' (小周/双休)
    """
    # 找到目标日期所在周的周一
    days_since_monday = target_date.weekday()
    current_week_monday = target_date - timedelta(days=days_since_monday)
    
    # 计算与基准周一的周数差
    delta_days = (current_week_monday - BASE_BIG_WEEK_START).days
    weeks_diff = delta_days // 7
    
    # 如果周数差是偶数，则与基准周相同（大周）；奇数则相反（小周）
    # 注意：这里假设 BASE_BIG_WEEK_START 是大周
    if weeks_diff % 2 == 0:
        return 'BIG'
    else:
        return 'SMALL'

def create_ics():
    cal = Calendar()
    cal.add('prodid', '-//My Size-Week Calendar//cn//')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('method', 'PUBLISH')
    cal.add('x-wr-calname', CALENDAR_NAME)
    cal.add('x-wr-caldesc', CALENDAR_DESC)
    cal.add('x-wr-timezone', TIMEZONE)

    tz = pytz.timezone(TIMEZONE)
    
    # 生成从今天开始的未来事件
    today = datetime.now()
    start_date = today - timedelta(days=30) # 稍微包含一点过去，防止时区问题导致今天不显示
    end_date = today + timedelta(days=DAYS_RANGE)

    current_date = start_date
    
    while current_date <= end_date:
        # 我们只在每周的特定时间添加一个全天事件来提示这一周的属性
        # 策略：在每周一早上添加一个事件，提示整周的性质
        if current_date.weekday() == 0: # 0 is Monday
            week_type = get_week_type(current_date)
            
            if week_type == 'BIG':
                summary = "【大周】本周六需上班"
                description = "大周（单休），周六需要正常工作，周日休息。"
                # 可选：在大周的周六也加一个提醒事件
                saturday = current_date + timedelta(days=5)
                event_sat = Event()
                event_sat.add('summary', "🔴上班")
                event_sat.add('description', "大周工作日，请按时打卡。")
                event_sat.add('dtstart', saturday.date())
                event_sat.add('dtend', (saturday + timedelta(days=1)).date())
                event_sat.add('transp', 'TRANSPARENT') # 设为透明，不影响忙碌状态，仅提示
                cal.add_component(event_sat)
                
            else:
                summary = "【小周】本周双休"
                description = "今天是周一。本周为小周（双休），周六日均休息。"

            # 创建周一的主提示事件
            event = Event()
            event.add('summary', summary)
            event.add('description', description)
            event.add('dtstart', current_date.date())
            event.add('dtend', (current_date + timedelta(days=1)).date())
            event.add('transp', 'TRANSPARENT') # 透明事件，不会把周一标记为“忙碌”，仅作提示
            
            # 设置警报 (可选，周一早上8点提醒)
            from icalendar import Alarm
            alarm = Alarm()
            alarm.add('action', 'DISPLAY')
            alarm.add('description', summary)
            alarm.add('trigger', timedelta(hours=8)) # 周一早上8点触发
            event.add_component(alarm)
            
            cal.add_component(event)

        current_date += timedelta(days=1)

    return cal.to_ical().decode('utf-8')

if __name__ == '__main__':
    ics_content = create_ics()
    
    # 选项 A: 打印到控制台 (用于测试)
    print(ics_content[:500] + "...") 
    
    # 选项 B: 保存为本地文件 (用于上传到 GitHub Pages 等静态托管)
    with open('work_schedule.ics', 'w', encoding='utf-8') as f:
        f.write(ics_content)
    print("\n已成功生成 work_schedule.ics 文件。")
    
    # 选项 C: 如果是 Web 服务 (如 Flask)，可以直接 return ics_content
    # return Response(ics_content, mimetype='text/calendar')
