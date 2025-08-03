#!/usr/bin/env python3
"""
Advanced Search Functionality Demo

Demonstrates the comprehensive search and query capabilities
with filtering, sorting, pagination, and performance optimization.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.lead_database import get_lead_database
from database.search_engine import SearchQuery, SearchFilter, SortCriteria, ComparisonOperator, SortOrder

def demo_search_functionality():
    """Demonstrate advanced search capabilities"""
    print("🔍 Advanced Search Functionality Demo")
    print("=" * 42)
    
    # Get database instance
    db = get_lead_database()
    
    # Add comprehensive sample data
    print("\n📊 Adding sample data for search demonstration...")
    sample_leads = [
        {
            'full_name': 'John Smith',
            'email': 'john.smith@techcorp.com',
            'company': 'TechCorp Inc',
            'title': 'CEO',
            'location': 'Montreal, QC',
            'industry': 'Technology',
            'status': 'new',
            'verified': True,
            'enriched': False
        },
        {
            'full_name': 'Sarah Johnson',
            'email': 'sarah@innovate.co',
            'company': 'Innovate Solutions',
            'title': 'CTO',
            'location': 'Toronto, ON',
            'industry': 'Software',
            'status': 'contacted',
            'verified': False,
            'enriched': True
        },
        {
            'full_name': 'Mike Chen',
            'email': 'mike@startup.com',
            'company': 'StartupXYZ',
            'title': 'Founder',
            'location': 'Vancouver, BC',
            'industry': 'Fintech',
            'status': 'qualified',
            'verified': True,
            'enriched': True
        },
        {
            'full_name': 'Alice Brown',
            'email': 'alice@consulting.com',
            'company': 'Brown Consulting',
            'title': 'Principal',
            'location': 'Calgary, AB',
            'industry': 'Consulting',
            'status': 'new',
            'verified': False,
            'enriched': False
        },
        {
            'full_name': 'David Wilson',
            'email': 'david@techcorp.com',
            'company': 'TechCorp Inc',
            'title': 'VP Engineering',
            'location': 'Montreal, QC',
            'industry': 'Technology',
            'status': 'contacted',
            'verified': True,
            'enriched': False
        },
        {
            'full_name': 'Emma Davis',
            'email': 'emma@healthtech.com',
            'company': 'HealthTech Solutions',
            'title': 'Product Manager',
            'location': 'Toronto, ON',
            'industry': 'Healthcare',
            'status': 'new',
            'verified': False,
            'enriched': True
        }
    ]
    
    for lead_data in sample_leads:
        db.add_lead(lead_data)
    
    print(f"   ✅ Added {len(sample_leads)} sample leads")
    
    # Demo 1: Basic Search with Filters
    print("\n🔍 Demo 1: Basic Search with Filters")
    print("-" * 35)
    
    # Search for Technology industry leads
    filter_obj = SearchFilter('industry', ComparisonOperator.EQUALS, 'Technology')
    query = SearchQuery(filters=[filter_obj])
    
    result = db.advanced_search(query)
    
    print(f"   🎯 Technology industry leads: {len(result['leads'])} found")
    print(f"   ⏱️ Query time: {result['query_time_ms']:.2f}ms")
    
    for lead in result['leads']:
        print(f"      • {lead['full_name']} - {lead['title']} at {lead['company']}")
    
    # Demo 2: Multiple Filters with AND Logic
    print("\n🔍 Demo 2: Multiple Filters (AND Logic)")
    print("-" * 38)
    
    filters = [
        SearchFilter('verified', ComparisonOperator.EQUALS, True),
        SearchFilter('location', ComparisonOperator.LIKE, '%Montreal%')
    ]
    query = SearchQuery(filters=filters)
    
    result = db.advanced_search(query)
    
    print(f"   🎯 Verified leads in Montreal: {len(result['leads'])} found")
    
    for lead in result['leads']:
        print(f"      • {lead['full_name']} - Verified: {lead['verified']}, Location: {lead['location']}")
    
    # Demo 3: LIKE Search with Wildcards
    print("\n🔍 Demo 3: LIKE Search with Wildcards")
    print("-" * 35)
    
    filter_obj = SearchFilter('full_name', ComparisonOperator.LIKE, '%John%')
    query = SearchQuery(filters=[filter_obj])
    
    result = db.advanced_search(query)
    
    print(f"   🎯 Names containing 'John': {len(result['leads'])} found")
    
    for lead in result['leads']:
        print(f"      • {lead['full_name']} - {lead['company']}")
    
    # Demo 4: IN Operator for Multiple Values
    print("\n🔍 Demo 4: IN Operator for Multiple Values")
    print("-" * 40)
    
    filter_obj = SearchFilter('status', ComparisonOperator.IN, ['new', 'contacted'])
    query = SearchQuery(filters=[filter_obj])
    
    result = db.advanced_search(query)
    
    print(f"   🎯 Leads with status 'new' or 'contacted': {len(result['leads'])} found")
    
    for lead in result['leads']:
        print(f"      • {lead['full_name']} - Status: {lead['status']}")
    
    # Demo 5: Sorting and Ordering
    print("\n🔍 Demo 5: Sorting and Ordering")
    print("-" * 30)
    
    # Sort by company name ascending, then by full name
    sort_criteria = [
        SortCriteria('company', SortOrder.ASC),
        SortCriteria('full_name', SortOrder.ASC)
    ]
    query = SearchQuery(sort_by=sort_criteria)
    
    result = db.advanced_search(query)
    
    print(f"   📊 All leads sorted by company, then name:")
    
    for lead in result['leads']:
        print(f"      • {lead['company']} - {lead['full_name']}")
    
    # Demo 6: Pagination
    print("\n🔍 Demo 6: Pagination")
    print("-" * 20)
    
    # Get first page (2 results)
    query = SearchQuery(limit=2, offset=0)
    page1 = db.advanced_search(query)
    
    print(f"   📄 Page 1 (limit=2, offset=0): {len(page1['leads'])} results")
    print(f"   📊 Page info: {page1['page_info']}")
    
    for lead in page1['leads']:
        print(f"      • {lead['full_name']} - {lead['company']}")
    
    # Get second page
    query = SearchQuery(limit=2, offset=2)
    page2 = db.advanced_search(query)
    
    print(f"\n   📄 Page 2 (limit=2, offset=2): {len(page2['leads'])} results")
    
    for lead in page2['leads']:
        print(f"      • {lead['full_name']} - {lead['company']}")
    
    # Demo 7: Quick Search
    print("\n🔍 Demo 7: Quick Search Across Multiple Fields")
    print("-" * 45)
    
    search_results = db.quick_search('Tech', limit=10)
    
    print(f"   🚀 Quick search for 'Tech': {len(search_results)} results")
    
    for lead in search_results:
        print(f"      • {lead['full_name']} - {lead['company']} ({lead['industry']})")
    
    # Demo 8: Specialized Search Methods
    print("\n🔍 Demo 8: Specialized Search Methods")
    print("-" * 37)
    
    # Search by company
    company_results = db.search_by_company('TechCorp', exact_match=False)
    print(f"   🏢 Company search for 'TechCorp': {len(company_results)} results")
    
    # Search by location
    location_results = db.search_by_location('Toronto')
    print(f"   📍 Location search for 'Toronto': {len(location_results)} results")
    
    # Search by industry
    industry_results = db.search_by_industry('Technology')
    print(f"   🏭 Industry search for 'Technology': {len(industry_results)} results")
    
    # Get recent leads
    recent_results = db.get_recent_leads(days=1, limit=5)
    print(f"   🕐 Recent leads (last 1 day): {len(recent_results)} results")
    
    # Get enriched leads
    enriched_results = db.get_enriched_leads()
    print(f"   ✨ Enriched leads: {len(enriched_results)} results")
    
    # Get unverified leads
    unverified_results = db.get_unverified_leads()
    print(f"   ❓ Unverified leads: {len(unverified_results)} results")
    
    # Demo 9: Complex Query with Multiple Criteria
    print("\n🔍 Demo 9: Complex Query with Multiple Criteria")
    print("-" * 45)
    
    complex_filters = [
        SearchFilter('industry', ComparisonOperator.IN, ['Technology', 'Software', 'Fintech']),
        SearchFilter('verified', ComparisonOperator.EQUALS, True),
        SearchFilter('location', ComparisonOperator.LIKE, '%QC%')  # Quebec locations
    ]
    
    complex_sort = [
        SortCriteria('industry', SortOrder.ASC),
        SortCriteria('full_name', SortOrder.ASC)
    ]
    
    complex_query = SearchQuery(
        filters=complex_filters,
        sort_by=complex_sort,
        limit=10
    )
    
    complex_result = db.advanced_search(complex_query)
    
    print(f"   🎯 Complex search results: {len(complex_result['leads'])} found")
    print(f"   📊 Total matching records: {complex_result['total_count']}")
    print(f"   ⏱️ Query time: {complex_result['query_time_ms']:.2f}ms")
    
    for lead in complex_result['leads']:
        print(f"      • {lead['full_name']} - {lead['industry']} - {lead['location']}")
    
    # Demo 10: Search Statistics and Analytics
    print("\n📊 Demo 10: Search Statistics and Analytics")
    print("-" * 42)
    
    stats = db.get_search_statistics()
    
    print(f"   📈 Database Statistics:")
    print(f"      Total leads: {stats['total_leads']}")
    print(f"      Verified: {stats['verified_count']}")
    print(f"      Enriched: {stats['enriched_count']}")
    print(f"      Added this week: {stats['leads_added_this_week']}")
    
    print(f"\n   📊 Status Breakdown:")
    for status, count in stats['status_breakdown'].items():
        print(f"      {status}: {count}")
    
    print(f"\n   🏢 Top Companies:")
    for company, count in list(stats['top_companies'].items())[:5]:
        print(f"      {company}: {count} leads")
    
    print(f"\n   🏭 Top Industries:")
    for industry, count in list(stats['top_industries'].items())[:5]:
        print(f"      {industry}: {count} leads")
    
    print(f"\n   📍 Top Locations:")
    for location, count in list(stats['top_locations'].items())[:5]:
        print(f"      {location}: {count} leads")
    
    print("\n✅ Advanced search functionality demo completed!")

def demo_performance_features():
    """Demonstrate performance and optimization features"""
    print("\n⚡ Performance and Optimization Demo")
    print("=" * 37)
    
    db = get_lead_database()
    
    # Demo query performance
    print("\n⏱️ Query Performance Analysis")
    print("-" * 28)
    
    # Simple query
    start_time = datetime.now()
    simple_result = db.quick_search('Tech')
    simple_time = (datetime.now() - start_time).total_seconds() * 1000
    
    print(f"   🚀 Quick search: {simple_time:.2f}ms ({len(simple_result)} results)")
    
    # Complex query
    complex_filters = [
        SearchFilter('verified', ComparisonOperator.EQUALS, True),
        SearchFilter('industry', ComparisonOperator.LIKE, '%Tech%')
    ]
    complex_query = SearchQuery(filters=complex_filters)
    
    complex_result = db.advanced_search(complex_query)
    
    print(f"   🎯 Complex search: {complex_result['query_time_ms']:.2f}ms ({len(complex_result['leads'])} results)")
    
    # Pagination performance
    paginated_query = SearchQuery(limit=3, offset=0)
    paginated_result = db.advanced_search(paginated_query)
    
    print(f"   📄 Paginated search: {paginated_result['query_time_ms']:.2f}ms (page 1 of {paginated_result['page_info']['total_pages']})")
    
    # Index usage demonstration
    print(f"\n🔍 Index Usage Optimization:")
    print(f"   ✅ Indexed fields: full_name, email, linkedin_url, company, status")
    print(f"   ✅ Optimized queries use indexes for fast lookups")
    print(f"   ✅ LIKE queries with leading wildcards may be slower")
    
    print("\n✅ Performance demo completed!")

def main():
    """Main demo function"""
    try:
        demo_search_functionality()
        demo_performance_features()
        
        print("\n🎉 All search functionality demos completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)