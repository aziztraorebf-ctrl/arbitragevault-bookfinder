// Test: Verify Keepa API tokens are available
const { chromium } = require('playwright');

(async () => {
  console.log('=== KEEPA API TOKENS TEST ===\n');

  // Test backend directly
  console.log('1. Testing backend API directly...');

  try {
    const response = await fetch('http://localhost:8001/api/v1/niches/discover?count=1&shuffle=false');
    const data = await response.json();

    console.log('   Status:', response.status);
    console.log('   Niches count:', data.metadata?.niches_count || 0);

    if (data.metadata?.niches_count === 0) {
      console.log('   ❌ FAILED: No niches returned');

      // Check for rate limit in logs
      const healthResponse = await fetch('http://localhost:8001/api/v1/keepa/health');
      const healthData = await healthResponse.json();

      console.log('\n2. Keepa Health Check:');
      console.log('   Tokens remaining:', healthData.tokens_remaining || 'Unknown');
      console.log('   Status:', healthData.status || 'Unknown');

      if (healthData.tokens_remaining === 0) {
        console.log('\n   ⚠️  ROOT CAUSE: Keepa API rate limit reached (0 tokens)');
      }
    } else {
      console.log('   ✅ SUCCESS: Found', data.metadata.niches_count, 'niches');
    }

  } catch (error) {
    console.log('   ❌ ERROR:', error.message);
  }

  console.log('\n=== TEST COMPLETE ===');
})();