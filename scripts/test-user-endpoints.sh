#!/bin/bash

# Test User Endpoints - Production
# Usage: ./scripts/test-user-endpoints.sh

set -e

API_URL="https://api.envoyou.com"
echo "🧪 Testing User Endpoints on Production"
echo "API: $API_URL"
echo "=============================================="

# Test without authentication (should fail)
echo ""
echo "1. Testing endpoints without auth (should return 401/403):"
echo "-----------------------------------------------------------"

echo "GET /user/profile"
curl -s -w "Status: %{http_code}\n" "$API_URL/user/profile" | head -2

echo ""
echo "GET /user/calculations"
curl -s -w "Status: %{http_code}\n" "$API_URL/user/calculations" | head -2

echo ""
echo "GET /user/packages"
curl -s -w "Status: %{http_code}\n" "$API_URL/user/packages" | head -2

echo ""
echo "GET /user/notifications"
curl -s -w "Status: %{http_code}\n" "$API_URL/user/notifications" | head -2

echo ""
echo "GET /user/preferences"
curl -s -w "Status: %{http_code}\n" "$API_URL/user/preferences" | head -2

echo ""
echo "GET /user/activity"
curl -s -w "Status: %{http_code}\n" "$API_URL/user/activity" | head -2

echo ""
echo "2. Testing endpoint availability (should return proper error messages):"
echo "-----------------------------------------------------------------------"

echo "GET /user/calculations/123"
curl -s -w "Status: %{http_code}\n" "$API_URL/user/calculations/123" | head -2

echo ""
echo "GET /user/packages/123"
curl -s -w "Status: %{http_code}\n" "$API_URL/user/packages/123" | head -2

echo ""
echo "PUT /user/notifications/123/read"
curl -s -X PUT -w "Status: %{http_code}\n" "$API_URL/user/notifications/123/read" | head -2

echo ""
echo "PUT /user/preferences"
curl -s -X PUT -H "Content-Type: application/json" -d '{"timezone":"UTC"}' -w "Status: %{http_code}\n" "$API_URL/user/preferences" | head -2

echo ""
echo "3. Testing DELETE endpoints (should require auth):"
echo "--------------------------------------------------"

echo "DELETE /user/calculations/123"
curl -s -X DELETE -w "Status: %{http_code}\n" "$API_URL/user/calculations/123" | head -2

echo ""
echo "DELETE /user/packages/123"
curl -s -X DELETE -w "Status: %{http_code}\n" "$API_URL/user/packages/123" | head -2

echo ""
echo "DELETE /user/notifications/123"
curl -s -X DELETE -w "Status: %{http_code}\n" "$API_URL/user/notifications/123" | head -2

echo ""
echo "=============================================="
echo "✅ User Endpoints Test Complete"
echo ""
echo "📋 Expected Results:"
echo "- All endpoints should return 401/403 (authentication required)"
echo "- Error messages should be clear and helpful"
echo "- No 500 errors (indicates endpoints are properly registered)"
echo ""
echo "🔐 Next: Test with valid Supabase JWT token"
echo "=============================================="