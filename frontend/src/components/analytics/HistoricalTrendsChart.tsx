import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { useASINTrends } from '../../hooks/useProductDecision'
import { Loader2, AlertTriangle, TrendingDown, TrendingUp } from 'lucide-react'

interface HistoricalTrendsChartProps {
  asin: string
  days?: number
}

/**
 * Phase 8.0 Historical Trends Chart Component
 *
 * Displays time-series data for:
 * - BSR (Best Seller Rank) trends over time
 * - Price history and volatility
 * - Seller count evolution
 *
 * Uses Recharts for responsive visualization
 */
export function HistoricalTrendsChart({ asin, days = 90 }: HistoricalTrendsChartProps) {
  const {
    data: trends,
    isLoading,
    isError,
    error
  } = useASINTrends(asin, days)

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
        <div className="flex items-center justify-center space-x-3">
          <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
          <p className="text-gray-600">Loading trends...</p>
        </div>
      </div>
    )
  }

  if (isError || !trends) {
    return (
      <div className="bg-white rounded-lg shadow-md border border-yellow-200 p-6">
        <div className="flex items-center space-x-3">
          <AlertTriangle className="w-6 h-6 text-yellow-500" />
          <div>
            <p className="text-gray-700 font-medium">No historical data available</p>
            <p className="text-sm text-gray-600">
              {error instanceof Error ? error.message : 'Historical tracking not yet started for this ASIN'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-6">
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-lg font-bold text-gray-900 mb-2">Historical Trends</h3>
        <div className="flex items-center space-x-4 text-sm text-gray-600">
          <span>ASIN: {trends.asin}</span>
          <span>Data Points: {trends.data_points}</span>
          <span>Period: {days} days</span>
        </div>
      </div>

      {/* Trend Summary */}
      {trends.bsr && (
        <TrendSummary
          label="BSR Trend"
          trend={trends.bsr.trend}
          current={trends.bsr.current}
          change={trends.bsr.change}
          isRank={true}
        />
      )}
      {trends.price && (
        <TrendSummary
          label="Price Trend"
          current={trends.price.current}
          average={trends.price.average}
          volatility={trends.price.volatility}
        />
      )}

      {/* Charts Grid */}
      <div className="space-y-8 mt-6">
        {/* BSR Trend Chart */}
        {trends.bsr && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Best Seller Rank Over Time</h4>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart
                data={[
                  { date: 'Start', rank: trends.bsr.earliest },
                  { date: 'Current', rank: trends.bsr.current },
                ]}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis reversed={true} label={{ value: 'BSR (lower is better)', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="rank"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6', r: 4 }}
                  name="BSR"
                />
              </LineChart>
            </ResponsiveContainer>
            <div className="mt-2 text-xs text-gray-500">
              Best Rank: {trends.bsr.lowest_rank.toLocaleString()} | Worst Rank: {trends.bsr.highest_rank.toLocaleString()}
            </div>
          </div>
        )}

        {/* Price History Chart */}
        {trends.price && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Price History</h4>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart
                data={[
                  { date: 'Min', price: trends.price.min },
                  { date: 'Avg', price: trends.price.average },
                  { date: 'Max', price: trends.price.max },
                  { date: 'Current', price: trends.price.current },
                ]}
              >
                <defs>
                  <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.1}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis label={{ value: 'Price ($)', angle: -90, position: 'insideLeft' }} />
                <Tooltip formatter={(value: number) => `$${value.toFixed(2)}`} />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="price"
                  stroke="#10b981"
                  fillOpacity={1}
                  fill="url(#colorPrice)"
                  name="Price"
                />
              </AreaChart>
            </ResponsiveContainer>
            <div className="mt-2 text-xs text-gray-500">
              Volatility: ${trends.price.volatility.toFixed(2)} | Average: ${trends.price.average.toFixed(2)}
            </div>
          </div>
        )}

        {/* Seller Count Chart */}
        {trends.sellers && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Seller Count Evolution</h4>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart
                data={[
                  { date: 'Min', sellers: trends.sellers.min },
                  { date: 'Avg', sellers: trends.sellers.average },
                  { date: 'Max', sellers: trends.sellers.max },
                  { date: 'Current', sellers: trends.sellers.current },
                ]}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis label={{ value: 'Seller Count', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="sellers"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  dot={{ fill: '#f59e0b', r: 4 }}
                  name="Sellers"
                />
              </LineChart>
            </ResponsiveContainer>
            <div className="mt-2 text-xs text-gray-500">
              Trend: {trends.sellers.trend === 'increasing' ? 'More competition' : 'Less competition'}
            </div>
          </div>
        )}
      </div>

      {/* Footer Note */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          Historical data collected daily via Celery background jobs. Date range: {trends.date_range.start} to {trends.date_range.end}
        </p>
      </div>
    </div>
  )
}

/**
 * Trend Summary Component
 */
function TrendSummary({
  label,
  trend,
  current,
  change,
  average,
  volatility,
  isRank = false
}: {
  label: string
  trend?: 'improving' | 'declining' | 'increasing' | 'decreasing'
  current: number
  change?: number
  average?: number
  volatility?: number
  isRank?: boolean
}) {
  const isPositive = trend === 'improving' || trend === 'decreasing'
  const isNegative = trend === 'declining' || trend === 'increasing'

  const trendColor = isPositive ? 'text-green-600' : isNegative ? 'text-red-600' : 'text-gray-600'
  const TrendIcon = isPositive ? TrendingDown : isNegative ? TrendingUp : null

  return (
    <div className="bg-gray-50 rounded-lg p-4 mb-4 border border-gray-200">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-gray-700">{label}</p>
          <p className="text-2xl font-bold text-gray-900">
            {isRank ? current.toLocaleString() : `$${current.toFixed(2)}`}
          </p>
          {change !== undefined && (
            <p className={`text-sm ${trendColor} flex items-center mt-1`}>
              {TrendIcon && <TrendIcon className="w-4 h-4 mr-1" />}
              {isRank
                ? `${change > 0 ? '+' : ''}${change.toLocaleString()} since start`
                : `${change > 0 ? '+' : ''}$${change.toFixed(2)}`
              }
            </p>
          )}
          {average !== undefined && (
            <p className="text-xs text-gray-600 mt-1">
              Average: ${average.toFixed(2)}
            </p>
          )}
          {volatility !== undefined && (
            <p className="text-xs text-gray-600">
              Volatility: ${volatility.toFixed(2)}
            </p>
          )}
        </div>
        {trend && (
          <div className={`px-3 py-1 rounded-full text-xs font-semibold ${
            isPositive ? 'bg-green-100 text-green-700' :
            isNegative ? 'bg-red-100 text-red-700' :
            'bg-gray-100 text-gray-700'
          }`}>
            {trend.toUpperCase()}
          </div>
        )}
      </div>
    </div>
  )
}
