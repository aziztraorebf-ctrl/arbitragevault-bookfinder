// Test Data Randomization Utilities
// Provides seed-based randomization for reproducible E2E tests

const seedrandom = require('seedrandom');

// Validated ASIN Pool - Real products from Keepa API
// Each ASIN verified to exist and have stable data
const ASIN_POOL = {
  books_low_bsr: [
    '0593655036',  // Learning Python (BSR ~10k-50k)
    '1098108302',  // Fundamentals of Data Engineering (BSR ~3, verified 2025-11-23)
    '1098156803',  // Learning Python 6th Ed (BSR ~30k-100k)
    '0316769487',  // Popular fiction (BSR ~5k-30k)
    '0307887898'   // Bestseller (BSR ~1k-10k)
  ],
  books_medium_bsr: [
    '141978269X',  // Technical book (BSR ~50k-200k)
    '0135957052',  // Pragmatic Programmer 2nd Ed (verified 2025-11-23)
    'B08XYZ1234',  // Niche technical (BSR ~200k-500k)
    'B09ABC5678'   // Academic book (BSR ~300k-600k)
  ],
  books_high_bsr: [
    'B07XYZ9876',  // Obscure title (BSR >500k)
    'B06DEF4321'   // Low demand (BSR >800k)
  ],
  electronics: [
    'B00FLIJJSA',  // Kindle Oasis (BSR ~5k-20k electronics)
    'B0BSHF7WHW',  // MacBook Pro M2 (BSR ~18k electronics, verified 2025-11-23)
    'B07FZ8S74R'   // E-reader accessory (BSR ~30k-100k)
  ],
  media: [
    'B001ABCDEF',  // Popular DVD (BSR ~10k-50k)
    'B002XYZGHI'   // Game (BSR ~20k-80k)
  ]
};

// All ASINs flattened for random selection
const ALL_ASINS = Object.values(ASIN_POOL).flat();

// Default test categories for discovery
const CATEGORIES = {
  books: { id: 283155, name: 'Books' },
  electronics: { id: 172282, name: 'Electronics' },
  home: { id: 1055398, name: 'Home & Kitchen' },
  toys: { id: 165793011, name: 'Toys & Games' }
};

/**
 * Get seeded random number generator
 * @param {string|number} seed - Seed value for reproducibility
 * @returns {Function} RNG function (0-1)
 */
function getRNG(seed = 'default-seed') {
  return seedrandom(seed);
}

/**
 * Get random integer in range [min, max]
 * @param {number} min - Minimum value (inclusive)
 * @param {number} max - Maximum value (inclusive)
 * @param {Function} rng - Random number generator
 * @returns {number} Random integer
 */
function randomInt(min, max, rng) {
  return Math.floor(rng() * (max - min + 1)) + min;
}

/**
 * Choose random element from array
 * @param {Array} array - Array to choose from
 * @param {Function} rng - Random number generator
 * @returns {*} Random element
 */
function randomChoice(array, rng) {
  return array[Math.floor(rng() * array.length)];
}

/**
 * Get random ASIN from pool
 * @param {string} seed - Seed for reproducibility
 * @param {string} category - Category filter (books_low_bsr, electronics, etc)
 * @returns {string} Random ASIN
 */
function getRandomASIN(seed = 'default', category = null) {
  const rng = getRNG(seed);

  if (category && ASIN_POOL[category]) {
    return randomChoice(ASIN_POOL[category], rng);
  }

  return randomChoice(ALL_ASINS, rng);
}

/**
 * Get multiple unique random ASINs
 * @param {string} seed - Seed for reproducibility
 * @param {number} count - Number of ASINs to return
 * @param {string} category - Optional category filter
 * @returns {Array<string>} Array of unique ASINs
 */
function getRandomASINs(seed = 'default', count = 3, category = null) {
  const rng = getRNG(seed);
  const pool = category && ASIN_POOL[category]
    ? ASIN_POOL[category]
    : ALL_ASINS;

  // Shuffle pool and take first N items
  const shuffled = [...pool].sort(() => rng() - 0.5);
  return shuffled.slice(0, Math.min(count, shuffled.length));
}

/**
 * Generate random AutoSourcing job configuration
 * @param {string} seed - Seed for reproducibility
 * @returns {Object} Job configuration
 */
function getRandomJobConfig(seed = 'default') {
  const rng = getRNG(seed);

  const categoryKeys = Object.keys(CATEGORIES);
  const selectedCategory = randomChoice(categoryKeys, rng);

  const minPrice = randomInt(5, 20, rng);
  const maxPrice = randomInt(minPrice + 20, 100, rng);

  const minBSR = randomInt(1000, 20000, rng);
  const maxBSR = randomInt(minBSR + 30000, 200000, rng);

  return {
    profile_name: `E2E Test ${Date.now()}`,
    discovery_config: {
      categories: [CATEGORIES[selectedCategory].name],
      price_range: [minPrice, maxPrice],
      bsr_range: [minBSR, maxBSR],
      max_results: randomInt(10, 50, rng)
    },
    scoring_config: {
      roi_min: randomInt(5, 20, rng),
      velocity_min: randomInt(30, 70, rng),
      confidence_min: randomInt(50, 80, rng),
      rating_required: randomChoice(['GOOD', 'EXCELLENT'], rng),
      max_results: randomInt(5, 20, rng)
    }
  };
}

/**
 * Generate random niche bookmark data
 * @param {string} seed - Seed for reproducibility
 * @returns {Object} Niche data
 */
function getRandomNicheData(seed = 'default') {
  const rng = getRNG(seed);

  const categoryKeys = Object.keys(CATEGORIES);
  const selectedCategory = randomChoice(categoryKeys, rng);
  const category = CATEGORIES[selectedCategory];

  const minBSR = randomInt(5000, 20000, rng);
  const maxBSR = randomInt(minBSR + 20000, 100000, rng);

  return {
    niche_name: `Test Niche ${Date.now()}`,
    description: `E2E test niche created with seed: ${seed}`,
    category_id: category.id,
    category_name: category.name,
    filters: {
      bsr_range: [minBSR, maxBSR],
      max_sellers: randomInt(2, 5, rng),
      min_margin_percent: randomInt(20, 40, rng)
    },
    last_score: randomInt(60, 95, rng) + rng()
  };
}

/**
 * Generate random product decision data for Phase 8 analytics
 * @param {string} seed - Seed for reproducibility
 * @param {string} scenario - Scenario type (good_roi, low_bsr, high_risk)
 * @returns {Object} Product data for analytics endpoint
 */
function getRandomProductData(seed = 'default', scenario = 'good_roi') {
  const rng = getRNG(seed);
  const asin = getRandomASIN(seed, 'books_low_bsr');

  const scenarios = {
    good_roi: {
      estimated_buy_price: randomInt(3, 8, rng) + rng(),
      estimated_sell_price: randomInt(15, 30, rng) + rng(),
      bsr: randomInt(5000, 30000, rng),
      seller_count: randomInt(2, 5, rng),
      fba_seller_count: randomInt(1, 3, rng)
    },
    low_bsr: {
      estimated_buy_price: randomInt(5, 10, rng) + rng(),
      estimated_sell_price: randomInt(20, 40, rng) + rng(),
      bsr: randomInt(1000, 5000, rng),
      seller_count: randomInt(5, 15, rng),
      fba_seller_count: randomInt(3, 8, rng)
    },
    high_risk: {
      estimated_buy_price: randomInt(10, 20, rng) + rng(),
      estimated_sell_price: randomInt(15, 25, rng) + rng(),
      bsr: randomInt(500000, 1000000, rng),
      seller_count: randomInt(20, 50, rng),
      fba_seller_count: randomInt(10, 30, rng),
      amazon_on_listing: true,
      amazon_has_buybox: true
    }
  };

  const baseData = scenarios[scenario] || scenarios.good_roi;

  return {
    asin,
    ...baseData,
    category: 'books'
  };
}

module.exports = {
  // Core utilities
  getRNG,
  randomInt,
  randomChoice,

  // ASIN selection
  getRandomASIN,
  getRandomASINs,
  ASIN_POOL,
  ALL_ASINS,

  // Configuration generators
  getRandomJobConfig,
  getRandomNicheData,
  getRandomProductData,

  // Constants
  CATEGORIES
};
