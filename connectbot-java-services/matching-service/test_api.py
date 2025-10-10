#!/usr/bin/env python3
"""
Тестирование ConnectBot Matching Service API
"""
import json
import requests
import time

# Конфигурация
BASE_URL = "http://localhost:8080"
API_BASE = f"{BASE_URL}/api/matching"

# Тестовые данные сотрудников
test_employees = [
    {
        "id": 1,
        "full_name": "Иван Иванов",
        "position": "Разработчик",
        "department": "IT", 
        "business_center": "БЦ Москва-Сити",
        "telegram_id": 123456789,
        "telegram_username": "ivan_dev",
        "interests": ["coffee", "chess", "games"],
        "is_active": True
    },
    {
        "id": 2,
        "full_name": "Мария Петрова",
        "position": "Дизайнер",
        "department": "Design",
        "business_center": "БЦ Москва-Сити", 
        "telegram_id": 987654321,
        "telegram_username": "maria_design",
        "interests": ["coffee", "photo", "lunch"],
        "is_active": True
    },
    {
        "id": 3,
        "full_name": "Алексей Сидоров",
        "position": "Аналитик", 
        "department": "Analytics",
        "business_center": "БЦ Белая Площадь",
        "telegram_id": 456789123,
        "telegram_username": "alex_analyst",
        "interests": ["coffee", "chess"],
        "is_active": True
    },
    {
        "id": 4,
        "full_name": "Елена Козлова",
        "position": "Менеджер",
        "department": "Management", 
        "business_center": "БЦ Белая Площадь",
        "telegram_id": 789123456,
        "telegram_username": "elena_pm",
        "interests": ["lunch", "walk", "masterclass"],
        "is_active": True
    },
    {
        "id": 5,
        "full_name": "Дмитрий Волков",
        "position": "DevOps",
        "department": "IT",
        "business_center": "БЦ Москва-Сити",
        "telegram_id": 321654987,
        "telegram_username": "dmitry_ops", 
        "interests": ["coffee", "games"],
        "is_active": True
    }
]

def print_separator(title):
    """Печать разделителя с заголовком"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def test_health_check():
    """Тестирование health check"""
    print_separator("🏥 HEALTH CHECK")
    
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Service: {health_data.get('service')}")
            print(f"✅ Status: {health_data.get('status')}")
            print(f"✅ Version: {health_data.get('version')}")
            
            redis_status = health_data.get('redis', {})
            print(f"Redis: {redis_status.get('status', 'N/A')}")
            
            memory = health_data.get('memory', {})
            if memory:
                print(f"Memory Usage: {memory.get('usage_percent', 'N/A')}%")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        print("Убедитесь, что сервис запущен на localhost:8080")
        return False
        
    return True

def test_algorithms_info():
    """Тестирование получения информации об алгоритмах"""
    print_separator("📋 ALGORITHMS INFO")
    
    try:
        response = requests.get(f"{API_BASE}/algorithms")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Available algorithms: {data.get('total')}")
            
            algorithms = data.get('algorithms', {})
            for alg_name, alg_info in algorithms.items():
                print(f"  • {alg_info.get('name')} ({alg_name})")
                print(f"    {alg_info.get('description')}")
                print(f"    Endpoint: {alg_info.get('endpoint')}")
        else:
            print(f"❌ Failed: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")

def test_simple_matching():
    """Тестирование простого matching"""
    print_separator("🎲 SIMPLE MATCHING")
    
    try:
        response = requests.post(
            f"{API_BASE}/coffee/simple",
            json=test_employees,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Algorithm: {result.get('algorithm')}")
            print(f"✅ Total employees: {result.get('total_employees')}")
            print(f"✅ Total pairs: {result.get('total_pairs')}")
            print(f"✅ Success rate: {result.get('success_rate')}%")
            
            pairs = result.get('pairs', [])
            print(f"\n👥 Pairs created ({len(pairs)}):")
            for i, pair in enumerate(pairs, 1):
                emp1 = pair['employee1']
                emp2 = pair['employee2']
                print(f"  {i}. {emp1['full_name']} & {emp2['full_name']}")
                print(f"     {emp1['position']} ({emp1['department']}) & {emp2['position']} ({emp2['department']})")
            
            unmatched = result.get('unmatched', [])
            if unmatched:
                print(f"\n😔 Unmatched ({len(unmatched)}):")
                for emp in unmatched:
                    print(f"  • {emp['full_name']} - {emp['position']}")
        else:
            print(f"❌ Failed: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")

def test_interest_based_matching():
    """Тестирование matching по интересам"""
    print_separator("☕ INTEREST-BASED MATCHING")
    
    try:
        response = requests.post(
            f"{API_BASE}/coffee/interest?interest=coffee",
            json=test_employees,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Algorithm: {result.get('algorithm')}")
            print(f"✅ Interest filter: coffee")
            print(f"✅ Matched employees: {result.get('total_pairs', 0) * 2}")
            print(f"✅ Success rate: {result.get('success_rate')}%")
            
            pairs = result.get('pairs', [])
            print(f"\n👥 Coffee pairs ({len(pairs)}):")
            for i, pair in enumerate(pairs, 1):
                emp1 = pair['employee1']
                emp2 = pair['employee2']
                print(f"  {i}. {emp1['full_name']} & {emp2['full_name']}")
                
                # Проверяем общие интересы
                common_interests = set(emp1.get('interests', [])) & set(emp2.get('interests', []))
                if common_interests:
                    print(f"     Общие интересы: {', '.join(common_interests)}")
                    
        else:
            print(f"❌ Failed: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")

def test_cross_department_matching():
    """Тестирование межотдельческого matching"""
    print_separator("🏢 CROSS-DEPARTMENT MATCHING")
    
    try:
        response = requests.post(
            f"{API_BASE}/coffee/cross-department",
            json=test_employees,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Algorithm: {result.get('algorithm')}")
            print(f"✅ Total pairs: {result.get('total_pairs')}")
            print(f"✅ Success rate: {result.get('success_rate')}%")
            
            pairs = result.get('pairs', [])
            print(f"\n👥 Cross-department pairs ({len(pairs)}):")
            for i, pair in enumerate(pairs, 1):
                emp1 = pair['employee1']
                emp2 = pair['employee2'] 
                dept1 = emp1.get('department', 'N/A')
                dept2 = emp2.get('department', 'N/A')
                
                print(f"  {i}. {emp1['full_name']} ({dept1}) & {emp2['full_name']} ({dept2})")
                
                if dept1 == dept2:
                    print(f"     ⚠️  WARNING: Same department!")
                else:
                    print(f"     ✅ Different departments: {dept1} ↔ {dept2}")
                    
        else:
            print(f"❌ Failed: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")

def test_performance():
    """Тестирование производительности"""
    print_separator("⚡ PERFORMANCE TEST")
    
    # Создаем большой список сотрудников
    large_employee_list = []
    for i in range(100):
        emp = {
            "id": i + 1,
            "full_name": f"Employee {i+1}",
            "position": f"Position {i % 10}",
            "department": f"Dept{i % 5}",
            "business_center": f"BC{i % 3}",
            "telegram_id": 1000000 + i,
            "telegram_username": f"user{i+1}",
            "interests": ["coffee", "lunch"][i % 2:i % 2 + 1],
            "is_active": True
        }
        large_employee_list.append(emp)
    
    print(f"Testing with {len(large_employee_list)} employees...")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{API_BASE}/coffee/simple",
            json=large_employee_list,
            headers={"Content-Type": "application/json"}
        )
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"⏱️  Response time: {duration:.3f} seconds")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Processed: {result.get('total_employees')} employees")
            print(f"✅ Created: {result.get('total_pairs')} pairs")
            print(f"✅ Throughput: {result.get('total_employees', 0) / duration:.1f} employees/sec")
        else:
            print(f"❌ Failed: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")

def main():
    """Основная функция тестирования"""
    print("🧪 ConnectBot Matching Service API Test Suite")
    print("=" * 60)
    
    # 1. Health Check
    if not test_health_check():
        print("\n❌ Service is not available. Exiting...")
        return
    
    # 2. Algorithms Info
    test_algorithms_info()
    
    # 3. Simple Matching
    test_simple_matching()
    
    # 4. Interest-based Matching
    test_interest_based_matching()
    
    # 5. Cross-department Matching  
    test_cross_department_matching()
    
    # 6. Performance Test
    test_performance()
    
    print_separator("🎉 TESTING COMPLETE")
    print("All tests finished!")
    print("\nNext steps:")
    print("• Check service logs for any errors")
    print("• Monitor memory usage during high load")
    print("• Test with Redis integration")
    print("• Set up production monitoring")

if __name__ == "__main__":
    main()