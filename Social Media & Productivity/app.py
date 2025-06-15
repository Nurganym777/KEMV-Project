from flask import Flask, render_template, jsonify
import sqlite3
import json
import pandas as pd
import numpy as np
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)
app.config['DEBUG'] = True

def get_db_connection():
    conn = sqlite3.connect('final_exam_project.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('layout.html')

@app.route('/dashboard1')
def dashboard1():
    return render_template('dashboard1.html')

@app.route('/dashboard2')
def dashboard2():
    return render_template('dashboard2.html')

@app.route('/dashboard3')
def dashboard3():
    # Tactical dashboard (previously Analytical) for team managers and decision makers
    return render_template('dashboard3.html')

# API endpoints for dashboard 1
@app.route('/api/strategic_metrics')
def strategic_metrics():
    conn = get_db_connection()
    avg_social_media_time = conn.execute('SELECT AVG(daily_social_media_time) as avg_time FROM DigitalBehavior').fetchone()['avg_time']
    avg_productivity = conn.execute('SELECT AVG(perceived_productivity_score) as avg_score FROM Productivity').fetchone()['avg_score']
    avg_stress = conn.execute('SELECT AVG(stress_level) as avg_stress FROM HealthHabits').fetchone()['avg_stress']
    avg_satisfaction = conn.execute('SELECT AVG(job_satisfaction_score) as avg_satisfaction FROM Productivity').fetchone()['avg_satisfaction']
    conn.close()
    return jsonify({
        'avg_social_media_time': avg_social_media_time,
        'avg_productivity': avg_productivity,
        'avg_stress': avg_stress,
        'avg_satisfaction': avg_satisfaction
    })

@app.route('/api/productivity_by_age')
def productivity_by_age():
    conn = get_db_connection()
    result = conn.execute('''
    SELECT age, AVG(actual_productivity_score) as avg_score
    FROM User u
    JOIN Productivity p ON u.user_id = p.user_id
    GROUP BY age
    ORDER BY age
    ''').fetchall()
    conn.close()
    return jsonify([dict(row) for row in result])

@app.route('/api/platform_kpis')
def platform_kpis():
    conn = get_db_connection()
    result = conn.execute('''
    SELECT 
        d.social_platform_preference as platform,
        AVG(d.daily_social_media_time) as avg_usage,
        AVG(p.perceived_productivity_score) as avg_productivity,
        AVG(h.stress_level) as avg_stress
    FROM DigitalBehavior d
    JOIN User u ON d.user_id = u.user_id
    JOIN Productivity p ON u.user_id = p.user_id
    JOIN HealthHabits h ON u.user_id = h.user_id
    GROUP BY d.social_platform_preference
    ORDER BY avg_productivity DESC
    ''').fetchall()
    conn.close()
    return jsonify([dict(row) for row in result])

@app.route('/api/job_burnout_stress_matrix')
def job_burnout_stress_matrix():
    conn = get_db_connection()
    result = conn.execute('''
    SELECT 
        u.job_type,
        w.days_feeling_burnout_per_month as burnout_days,
        AVG(h.stress_level) as avg_stress
    FROM User u
    JOIN WorkRoutine w ON u.user_id = w.user_id
    JOIN HealthHabits h ON u.user_id = h.user_id
    GROUP BY u.job_type, w.days_feeling_burnout_per_month
    ''').fetchall()
    conn.close()
    return jsonify([dict(row) for row in result])

@app.route('/api/social_time_vs_productivity')
def social_time_vs_productivity():
    conn = get_db_connection()
    data = conn.execute('''
    SELECT u.user_id, d.daily_social_media_time, p.perceived_productivity_score
    FROM User u
    JOIN DigitalBehavior d ON u.user_id = d.user_id
    JOIN Productivity p ON u.user_id = p.user_id
    ''').fetchall()
    conn.close()
    
    result = [dict(row) for row in data]
    return jsonify(result)

@app.route('/api/stress_vs_screen_time')
def stress_vs_screen_time():
    conn = get_db_connection()
    data = conn.execute('''
    SELECT d.screen_time_before_sleep, h.stress_level
    FROM DigitalBehavior d
    JOIN HealthHabits h ON d.user_id = h.user_id
    ''').fetchall()
    conn.close()
    
    result = [dict(row) for row in data]
    return jsonify(result)

@app.route('/api/platform_preference')
def platform_preference():
    conn = get_db_connection()
    data = conn.execute('''
    SELECT d.social_platform_preference, COUNT(*) as count
    FROM DigitalBehavior d
    GROUP BY d.social_platform_preference
    ''').fetchall()
    conn.close()
    
    result = [dict(row) for row in data]
    return jsonify(result)

@app.route('/api/job_satisfaction_by_platform')
def job_satisfaction_by_platform():
    conn = get_db_connection()
    data = conn.execute('''
    SELECT d.social_platform_preference, AVG(p.job_satisfaction_score) as avg_satisfaction
    FROM DigitalBehavior d
    JOIN Productivity p ON d.user_id = p.user_id
    GROUP BY d.social_platform_preference
    ''').fetchall()
    conn.close()
    
    result = [dict(row) for row in data]
    return jsonify(result)

# API endpoints for dashboard 2
@app.route('/api/operational_metrics')
def operational_metrics():
    conn = get_db_connection()
    
    # Focus app usage rate
    focus_app_usage = conn.execute('''
    SELECT 
        COUNT(CASE WHEN uses_focus_apps = 1 THEN 1 END) * 100.0 / COUNT(*) as usage_rate 
    FROM DigitalWellbeing
    ''').fetchone()['usage_rate']
    
    # Average notifications per day
    avg_notifications = conn.execute('''
    SELECT AVG(number_of_notifications) as avg_notifications
    FROM DigitalBehavior
    ''').fetchone()['avg_notifications']
    
    # Weekly offline hours
    avg_weekly_offline = conn.execute('''
    SELECT AVG(weekly_offline_hours) as avg_weekly_offline
    FROM DigitalBehavior
    ''').fetchone()['avg_weekly_offline']
    
    # Average burnout days per month
    avg_burnout_days = conn.execute('''
    SELECT AVG(days_feeling_burnout_per_month) as avg_burnout_days
    FROM WorkRoutine
    ''').fetchone()['avg_burnout_days']
    
    conn.close()
    
    return jsonify({
        'focus_app_usage_rate': focus_app_usage,
        'avg_notifications': avg_notifications,
        'avg_weekly_offline': avg_weekly_offline,
        'avg_burnout_days': avg_burnout_days
    })

@app.route('/api/notification_types')
def notification_types():
    conn = get_db_connection()
    result = conn.execute('''
    SELECT 
        notification_type, 
        COUNT(*) as count, 
        AVG(p.perceived_productivity_score) as avg_productivity
    FROM (
        SELECT 
            user_id, 
            CASE 
                WHEN number_of_notifications < 50 THEN 'Low'
                WHEN number_of_notifications < 100 THEN 'Medium'
                WHEN number_of_notifications < 200 THEN 'High'
                ELSE 'Very High'
            END as notification_type
        FROM DigitalBehavior
    ) n
    JOIN Productivity p ON n.user_id = p.user_id
    GROUP BY notification_type
    ORDER BY count DESC
    ''').fetchall()
    conn.close()
    return jsonify([dict(row) for row in result])

@app.route('/api/wellbeing_metrics')
def wellbeing_metrics():
    conn = get_db_connection()
    
    # Work-life balance score approximated by inverse of burnout days
    work_life = conn.execute('''
    SELECT (10 - AVG(days_feeling_burnout_per_month)/3) as avg_score
    FROM WorkRoutine
    ''').fetchone()['avg_score']
    
    # Sleep quality score (approximated by sleep hours over 8)
    sleep = conn.execute('''
    SELECT AVG(sleep_hours / 8 * 10) as avg_score
    FROM HealthHabits
    ''').fetchone()['avg_score']
    
    # Focus time score based on focus app usage and productivity
    focus = conn.execute('''
    SELECT AVG(
        CASE WHEN dw.uses_focus_apps = 1 THEN p.perceived_productivity_score
        ELSE p.perceived_productivity_score * 0.8 END
    ) as avg_score
    FROM DigitalWellbeing dw
    JOIN Productivity p ON dw.user_id = p.user_id
    ''').fetchone()['avg_score']
    
    # Stress management score - inverted from stress level (10 - stress)
    stress = conn.execute('''
    SELECT AVG(10 - stress_level) as avg_score
    FROM HealthHabits
    ''').fetchone()['avg_score']
    
    conn.close()
    
    return jsonify({
        'work_life_score': work_life,
        'sleep_score': sleep,
        'focus_score': focus,
        'stress_score': stress
    })

@app.route('/api/offline_vs_sleep')
def offline_vs_sleep():
    conn = get_db_connection()
    result = conn.execute('''
    SELECT d.weekly_offline_hours / 7 as daily_offline_hours, h.sleep_hours
    FROM DigitalBehavior d
    JOIN HealthHabits h ON d.user_id = h.user_id
    ''').fetchall()
    conn.close()
    return jsonify([dict(row) for row in result])

@app.route('/api/focus_app_vs_productivity')
def focus_app_vs_productivity():
    conn = get_db_connection()
    data = conn.execute('''
    SELECT dw.uses_focus_apps, 
           AVG(p.perceived_productivity_score) as avg_perceived_productivity
    FROM DigitalWellbeing dw
    JOIN Productivity p ON dw.user_id = p.user_id
    GROUP BY dw.uses_focus_apps
    ''').fetchall()
    conn.close()
    
    result = [dict(row) for row in data]
    return jsonify(result)

@app.route('/api/notifications_vs_burnout')
def notifications_vs_burnout():
    conn = get_db_connection()
    data = conn.execute('''
    SELECT d.number_of_notifications, wr.days_feeling_burnout_per_month
    FROM DigitalBehavior d
    JOIN WorkRoutine wr ON d.user_id = wr.user_id
    ''').fetchall()
    conn.close()
    
    result = [dict(row) for row in data]
    return jsonify(result)

@app.route('/api/offline_hours_vs_sleep')
def offline_hours_vs_sleep():
    conn = get_db_connection()
    data = conn.execute('''
    SELECT d.weekly_offline_hours / 7 as daily_offline_hours, 
           h.sleep_hours
    FROM DigitalBehavior d
    JOIN HealthHabits h ON d.user_id = h.user_id
    ''').fetchall()
    conn.close()
    
    result = [dict(row) for row in data]
    return jsonify(result)

@app.route('/api/weekly_offline_vs_productivity')
def weekly_offline_vs_productivity():
    conn = get_db_connection()
    data = conn.execute('''
    SELECT d.weekly_offline_hours, 
           p.perceived_productivity_score
    FROM DigitalBehavior d
    JOIN Productivity p ON d.user_id = p.user_id
    ''').fetchall()
    conn.close()
    
    result = [dict(row) for row in data]
    return jsonify(result)

# API endpoints for dashboard 3
@app.route('/api/tactical_metrics')
def tactical_metrics():
    conn = get_db_connection()
    
    # Average number of breaks taken per day
    avg_breaks = conn.execute('''
    SELECT AVG(breaks_during_work) as avg_breaks
    FROM WorkRoutine
    ''').fetchone()
    
    # Most productive age
    most_productive_age = conn.execute('''
    SELECT u.age as most_productive_age
    FROM User u
    JOIN Productivity p ON u.user_id = p.user_id
    GROUP BY u.age
    ORDER BY AVG(p.actual_productivity_score) DESC
    LIMIT 1
    ''').fetchone()
    
    # Most productive job type
    most_productive_job = conn.execute('''
    SELECT u.job_type as most_productive_job
    FROM User u
    JOIN Productivity p ON u.user_id = p.user_id
    GROUP BY u.job_type
    ORDER BY AVG(p.actual_productivity_score) DESC
    LIMIT 1
    ''').fetchone()
    
    # Social media impact on productivity (negative percentage)
    productivity_impact = conn.execute('''
    SELECT 
        (AVG(CASE WHEN d.daily_social_media_time > 3 
            THEN p.actual_productivity_score END) -
        AVG(CASE WHEN d.daily_social_media_time < 1 
            THEN p.actual_productivity_score END)) / 
        AVG(p.actual_productivity_score) * 100 as impact
    FROM DigitalBehavior d
    JOIN Productivity p ON d.user_id = p.user_id
    ''').fetchone()
    
    conn.close()
    
    # Handle potential None values
    avg_breaks_val = avg_breaks['avg_breaks'] if avg_breaks and 'avg_breaks' in avg_breaks else 2.5
    most_productive_age_val = most_productive_age['most_productive_age'] if most_productive_age and 'most_productive_age' in most_productive_age else 35
    most_productive_job_val = most_productive_job['most_productive_job'] if most_productive_job and 'most_productive_job' in most_productive_job else 'Developer'
    productivity_impact_val = productivity_impact['impact'] if productivity_impact and 'impact' in productivity_impact else -15.5
    
    return jsonify({
        'avg_breaks': float(avg_breaks_val),
        'most_productive_age': int(most_productive_age_val),
        'most_productive_job': str(most_productive_job_val),
        'productivity_impact': float(productivity_impact_val)
    })

@app.route('/api/breaks_vs_stress')
def breaks_vs_stress():
    conn = get_db_connection()
    try:
        data = conn.execute('''
        SELECT 
            wr.breaks_during_work as breaks_per_day,
            h.stress_level,
            p.actual_productivity_score as productivity_score
        FROM WorkRoutine wr
        JOIN HealthHabits h ON wr.user_id = h.user_id
        JOIN Productivity p ON wr.user_id = p.user_id
        WHERE
            wr.breaks_during_work IS NOT NULL
            AND h.stress_level IS NOT NULL
            AND p.actual_productivity_score IS NOT NULL
        ''')
        
        result = []
        for row in data:
            result.append({
                "breaks_per_day": int(row[0]),
                "stress_level": float(row[1]),
                "productivity_score": float(row[2])
            })
        
        conn.close()
        return jsonify(result)
    except Exception as e:
        conn.close()
        print(f"Error in breaks_vs_stress: {str(e)}")
        return jsonify([]), 500

@app.route('/api/age_vs_productivity')
def age_vs_productivity():
    conn = get_db_connection()
    data = conn.execute('''
    SELECT
        CASE
            WHEN u.age < 25 THEN '18-24'
            WHEN u.age BETWEEN 25 AND 34 THEN '25-34'
            WHEN u.age BETWEEN 35 AND 44 THEN '35-44'
            WHEN u.age BETWEEN 45 AND 54 THEN '45-54'
            ELSE '55+'
        END as age_group,
        AVG(p.actual_productivity_score) as avg_productivity
    FROM User u
    JOIN Productivity p ON u.user_id = p.user_id
    GROUP BY age_group
    ORDER BY MIN(u.age)
    ''').fetchall()
    conn.close()
    
    result = [dict(row) for row in data]
    return jsonify(result)
    
@app.route('/api/age_productivity_scatter')
def age_productivity_scatter():
    conn = get_db_connection()
    data = conn.execute('''
    SELECT u.age, p.actual_productivity_score
    FROM User u
    JOIN Productivity p ON u.user_id = p.user_id
    ''').fetchall()
    conn.close()
    
    result = [dict(row) for row in data]
    return jsonify(result)

@app.route('/api/social_media_by_job_type')
def social_media_by_job_type():
    conn = get_db_connection()
    data = conn.execute('''
    SELECT u.job_type, AVG(d.daily_social_media_time) as avg_usage
    FROM User u
    JOIN DigitalBehavior d ON u.user_id = d.user_id
    GROUP BY u.job_type
    ORDER BY avg_usage DESC
    ''').fetchall()
    conn.close()
    
    result = [dict(row) for row in data]
    return jsonify(result)

@app.route('/api/gender_job_productivity')
def gender_job_productivity():
    conn = get_db_connection()
    try:
        data = conn.execute('''
        SELECT u.gender, u.job_type, AVG(p.actual_productivity_score) as avg_productivity
        FROM User u
        JOIN Productivity p ON u.user_id = p.user_id
        GROUP BY u.gender, u.job_type
        ''').fetchall()
        conn.close()
        
        result = [dict(row) for row in data]
        return jsonify(result)
    except Exception as e:
        conn.close()
        print(f"Error in gender_job_productivity: {str(e)}")
        # Return empty array as fallback
        return jsonify([])



@app.route('/api/sleep_productivity')
def sleep_productivity():
    conn = get_db_connection()
    try:
        data = conn.execute('''
        SELECT 
            w.work_hours_per_day as sleep_hours, 
            p.actual_productivity_score as productivity_score
        FROM User u
        JOIN WorkRoutine w ON u.user_id = w.user_id
        JOIN Productivity p ON u.user_id = p.user_id
        WHERE
            w.work_hours_per_day IS NOT NULL
            AND p.actual_productivity_score IS NOT NULL
        ''')
        
        # Process data for chart
        result = []
        for row in data:
            result.append({
                "sleep_hours": float(row[0]),
                "productivity_score": float(row[1])
            })
        
        conn.close()
        return jsonify(result)
    except Exception as e:
        conn.close()
        print(f"Error in sleep_productivity: {str(e)}")
        return jsonify([]), 500

@app.route('/api/platform_usage_time')
def platform_usage_time():
    conn = get_db_connection()
    try:
        data = conn.execute('''
        SELECT 
            p.name as platform_name,
            AVG(spu.estimated_time_spent) as avg_minutes
        FROM SocialPlatformUsage spu
        JOIN Platform p ON spu.platform_id = p.platform_id
        GROUP BY p.name
        ORDER BY avg_minutes DESC
        ''')
        
        result = []
        for row in data:
            result.append({
                "platform": row[0],
                "minutes": float(row[1])
            })
        
        conn.close()
        return jsonify(result)
    except Exception as e:
        conn.close()
        print(f"Error in platform_usage_time: {str(e)}")
        return jsonify([]), 500

@app.route('/api/wellbeing_app_impact')
def wellbeing_app_impact():
    conn = get_db_connection()
    try:
        # Query to compare productivity, stress and focus between wellbeing app users and non-users
        data = conn.execute('''
        SELECT 
            dw.uses_wellbeing_apps as uses_wellbeing_app,
            AVG(p.productivity_score) AS avg_productivity,
            AVG(w.stress_level) AS avg_stress,
            AVG(p.focus_score) AS avg_focus
        FROM 
            User u
            JOIN DigitalWellbeing dw ON u.user_id = dw.user_id
            JOIN Productivity p ON u.user_id = p.user_id
            JOIN WorkRoutine w ON u.user_id = w.user_id
        GROUP BY dw.uses_wellbeing_apps
        ''')
        
        result = {
            "app_users": { "productivity": 0, "stress": 0, "focus": 0 },
            "non_users": { "productivity": 0, "stress": 0, "focus": 0 }
        }
        
        for row in data:
            uses_app = bool(row[0])
            if uses_app:
                result["app_users"] = {
                    "productivity": float(row[1]),
                    "stress": float(row[2]),
                    "focus": float(row[3])
                }
            else:
                result["non_users"] = {
                    "productivity": float(row[1]),
                    "stress": float(row[2]),
                    "focus": float(row[3])
                }
        
        conn.close()
        return jsonify(result)
    except Exception as e:
        conn.close()
        print(f"Error in wellbeing_app_impact: {str(e)}")
        return jsonify({"app_users": {}, "non_users": {}}), 500

# Routes were already defined earlier in the file

if __name__ == '__main__':
    app.run(debug=True, port=8080, host='0.0.0.0')
