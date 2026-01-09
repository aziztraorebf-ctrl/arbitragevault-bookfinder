// Sparkline - Mini line chart for KPI cards
// Elegant, minimal SVG visualization

interface SparklineProps {
  data: number[]
  width?: number
  height?: number
  className?: string
}

export function Sparkline({
  data,
  width = 80,
  height = 32,
  className = ''
}: SparklineProps) {
  if (data.length < 2) return null

  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1

  // Add padding to prevent clipping
  const padding = 2
  const chartWidth = width - padding * 2
  const chartHeight = height - padding * 2

  const points = data.map((value, index) => {
    const x = padding + (index / (data.length - 1)) * chartWidth
    const y = padding + chartHeight - ((value - min) / range) * chartHeight
    return `${x},${y}`
  }).join(' ')

  // Create path for area fill
  const areaPath = `M ${padding},${height - padding} L ${points.split(' ').join(' L ')} L ${width - padding},${height - padding} Z`

  return (
    <svg
      width={width}
      height={height}
      className={className}
      viewBox={`0 0 ${width} ${height}`}
      aria-hidden="true"
    >
      {/* Area fill */}
      <path
        d={areaPath}
        fill="var(--sparkline-fill)"
        opacity="0.5"
      />
      {/* Line */}
      <polyline
        fill="none"
        stroke="var(--sparkline-stroke)"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
      {/* End dot */}
      <circle
        cx={width - padding}
        cy={padding + chartHeight - ((data[data.length - 1] - min) / range) * chartHeight}
        r="3"
        fill="var(--sparkline-stroke)"
      />
    </svg>
  )
}
