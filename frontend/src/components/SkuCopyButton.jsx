import { useState } from 'react'

export default function SkuCopyButton({ sku, className = '' }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = (e) => {
    e.stopPropagation()
    navigator.clipboard.writeText(sku).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }

  return (
    <button
      className={`sku-copy-btn ${className}`}
      onClick={handleCopy}
      title="Copy SKU to clipboard"
      type="button"
    >
      {copied ? 'Copied!' : '📋'}
    </button>
  )
}
