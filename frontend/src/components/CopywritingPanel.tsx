import { useState } from 'react'
import { Copy, Check, RefreshCw, FileText, Globe } from 'lucide-react'

interface CopywritingPanelProps {
  imageDescription?: string
  onGenerate?: (platform: string) => void
}

interface GeneratedCopy {
  title: string
  bullets: string[]
  description: string
}

const platforms = [
  { id: 'amazon', name: '亚马逊', icon: '📦' },
  { id: 'tiktok', name: 'TikTok', icon: '🎵' },
  { id: 'instagram', name: 'Instagram', icon: '📷' },
  { id: '独立站', name: '独立站', icon: '🛒' }
]

export default function CopywritingPanel({ imageDescription, onGenerate }: CopywritingPanelProps) {
  const [selectedPlatform, setSelectedPlatform] = useState('amazon')
  const [isGenerating, setIsGenerating] = useState(false)
  const [copies, setCopies] = useState<GeneratedCopy[]>([])
  const [keywords, setKeywords] = useState<string[]>([])
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null)

  const handleGenerate = async () => {
    setIsGenerating(true)

    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 2000))

    // Mock generated copy
    const mockCopies: GeneratedCopy[] = [
      {
        title: '[Brand] Premium Product - Your Best Choice | Top Rated',
        bullets: [
          'Premium quality materials for lasting durability',
          'Elegant design that complements any style',
          'Customer favorite with thousands of reviews',
          'Perfect gift for friends and family'
        ],
        description: `Introducing our premium product, designed to exceed your expectations. Crafted with precision and care, this item delivers exceptional value. Experience the difference today with our top-rated offering.`
      },
      {
        title: 'Must-Have Item - Limited Edition Release',
        bullets: [
          'Exclusive design you won\'t find anywhere else',
          'Superior craftsmanship and attention to detail',
          'Versatile functionality for everyday use',
          'Satisfaction guaranteed or your money back'
        ],
        description: `You\'ve found the perfect solution! This must-have item combines style, functionality, and quality. Don\'t miss out on this limited edition release.`
      }
    ]

    const mockKeywords = [
      'Premium Quality', 'Best Seller', 'Customer Favorite',
      'Must-Have', 'Limited Edition', 'Top Rated'
    ]

    setCopies(mockCopies)
    setKeywords(mockKeywords)
    setIsGenerating(false)

    if (onGenerate) {
      onGenerate(selectedPlatform)
    }
  }

  const copyToClipboard = async (text: string, index: number) => {
    await navigator.clipboard.writeText(text)
    setCopiedIndex(index)
    setTimeout(() => setCopiedIndex(null), 2000)
  }

  const copyAll = async (copy: GeneratedCopy) => {
    const fullText = `${copy.title}\n\n${copy.bullets.map(b => `• ${b}`).join('\n')}\n\n${copy.description}`
    await navigator.clipboard.writeText(fullText)
    setCopiedIndex(-1)
    setTimeout(() => setCopiedIndex(null), 2000)
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-100">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
            <FileText className="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">智能文案生成</h3>
            <p className="text-sm text-gray-500">基于AI生成营销文案</p>
          </div>
        </div>
      </div>

      {/* Platform Selection */}
      <div className="px-6 py-4 border-b border-gray-100">
        <label className="block text-sm font-medium text-gray-700 mb-3">
          <Globe className="w-4 h-4 inline mr-1" />
          选择目标平台
        </label>
        <div className="flex gap-2">
          {platforms.map(platform => (
            <button
              key={platform.id}
              onClick={() => setSelectedPlatform(platform.id)}
              className={`
                flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all
                ${selectedPlatform === platform.id
                  ? 'bg-purple-100 text-purple-700 border-2 border-purple-300'
                  : 'bg-gray-50 text-gray-600 border-2 border-transparent hover:bg-gray-100'
                }
              `}
            >
              <span className="mr-1">{platform.icon}</span>
              {platform.name}
            </button>
          ))}
        </div>
      </div>

      {/* Generate Button */}
      <div className="px-6 py-4 border-b border-gray-100">
        <button
          onClick={handleGenerate}
          disabled={isGenerating}
          className={`
            w-full py-3 rounded-xl font-medium transition-all flex items-center justify-center gap-2
            ${isGenerating
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'bg-purple-600 hover:bg-purple-700 text-white shadow-lg'
            }
          `}
        >
          {isGenerating ? (
            <>
              <RefreshCw className="w-5 h-5 animate-spin" />
              生成中...
            </>
          ) : (
            <>
              <FileText className="w-5 h-5" />
              生成营销文案
            </>
          )}
        </button>
      </div>

      {/* Generated Content */}
      {copies.length > 0 && (
        <div className="divide-y divide-gray-100">
          {/* Keywords */}
          <div className="px-6 py-4 bg-gray-50">
            <p className="text-xs font-medium text-gray-500 mb-2">SEO关键词</p>
            <div className="flex flex-wrap gap-2">
              {keywords.map((keyword, idx) => (
                <span
                  key={idx}
                  className="px-2 py-1 bg-white rounded-full text-xs text-gray-600 border border-gray-200"
                >
                  {keyword}
                </span>
              ))}
            </div>
          </div>

          {/* Copies */}
          {copies.map((copy, idx) => (
            <div key={idx} className="p-6">
              <div className="flex items-start justify-between mb-3">
                <h4 className="font-medium text-gray-900">版本 {idx + 1}</h4>
                <div className="flex gap-1">
                  <button
                    onClick={() => copyToClipboard(copy.title, idx)}
                    className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600"
                    title="复制标题"
                  >
                    {copiedIndex === idx ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
                  </button>
                  <button
                    onClick={() => copyAll(copy)}
                    className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600"
                    title="复制全部"
                  >
                    {copiedIndex === -1 ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <h5 className="font-medium text-gray-800 mb-2">{copy.title}</h5>

              <ul className="space-y-1 mb-3">
                {copy.bullets.map((bullet, bIdx) => (
                  <li key={bIdx} className="text-sm text-gray-600 flex items-start gap-2">
                    <span className="text-purple-400 mt-1">•</span>
                    {bullet}
                  </li>
                ))}
              </ul>

              <p className="text-sm text-gray-500 leading-relaxed">
                {copy.description}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {copies.length === 0 && !isGenerating && (
        <div className="px-6 py-12 text-center">
          <FileText className="w-12 h-12 mx-auto text-gray-300 mb-3" />
          <p className="text-gray-500">点击上方按钮生成营销文案</p>
          <p className="text-sm text-gray-400 mt-1">支持亚马逊、TikTok、Instagram等平台</p>
        </div>
      )}
    </div>
  )
}
