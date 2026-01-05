import { useState } from 'react'
import { Wand2, Type, Image as ImageIcon, Layers, Check, ChevronDown } from 'lucide-react'

interface ProcessingOption {
  id: string
  name: string
  description: string
  icon: React.ReactNode
}

interface BackgroundStyle {
  id: string
  name: string
  description: string
  preview: string
}

const processingOptions: ProcessingOption[] = [
  {
    id: 'text_removal',
    name: '智能去文字',
    description: '自动检测并移除水印、文字',
    icon: <Type className="w-5 h-5" />
  },
  {
    id: 'background_replacement',
    name: '背景重绘',
    description: '欧美风格背景生成',
    icon: <ImageIcon className="w-5 h-5" />
  },
  {
    id: 'subject_segmentation',
    name: '主体分割',
    description: '精确提取产品主体',
    icon: <Layers className="w-5 h-5" />
  }
]

const backgroundStyles: BackgroundStyle[] = [
  { id: 'minimal_white', name: '极简白色', description: '干净的白色背景', preview: 'bg-white border' },
  { id: 'modern_home', name: '现代家居', description: '现代厨房、客厅场景', preview: 'bg-gradient-to-br from-amber-100 to-amber-200' },
  { id: 'business', name: '商业环境', description: '专业办公环境', preview: 'bg-gradient-to-br from-slate-100 to-slate-200' },
  { id: 'natural', name: '自然光线', description: '户外阳光场景', preview: 'bg-gradient-to-br from-green-100 to-green-200' },
  { id: 'amazon_standard', name: '亚马逊标准', description: '符合平台规范', preview: 'bg-white border' },
  { id: 'tiktok_vibrant', name: 'TikTok风格', description: '鲜艳色彩', preview: 'bg-gradient-to-r from-pink-500 to-purple-500' }
]

interface ProcessingControlProps {
  onProcess: (options: ProcessingOptions) => void
  isProcessing?: boolean
}

interface ProcessingOptions {
  operations: string[]
  backgroundStyle: string
  strength: number
}

export default function ProcessingControl({ onProcess, isProcessing = false }: ProcessingControlProps) {
  const [selectedOperations, setSelectedOperations] = useState<string[]>([])
  const [selectedBackground, setSelectedBackground] = useState<string>('minimal_white')
  const [strength, setStrength] = useState(0.8)
  const [showAdvanced, setShowAdvanced] = useState(false)

  const toggleOperation = (id: string) => {
    setSelectedOperations(prev =>
      prev.includes(id)
        ? prev.filter(op => op !== id)
        : [...prev, id]
    )
  }

  const handleProcess = () => {
    if (selectedOperations.length === 0) return
    onProcess({
      operations: selectedOperations,
      backgroundStyle: selectedBackground,
      strength
    })
  }

  return (
    <div className="space-y-6">
      {/* Processing Options */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">选择处理功能</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {processingOptions.map(option => (
            <button
              key={option.id}
              onClick={() => toggleOperation(option.id)}
              className={`
                relative p-4 rounded-xl border-2 text-left transition-all duration-200
                ${selectedOperations.includes(option.id)
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300 bg-white'
                }
              `}
            >
              <div className={`
                absolute top-4 right-4 w-6 h-6 rounded-full border-2 flex items-center justify-center
                ${selectedOperations.includes(option.id)
                  ? 'border-primary-500 bg-primary-500'
                  : 'border-gray-300'
                }
              `}>
                {selectedOperations.includes(option.id) && (
                  <Check className="w-4 h-4 text-white" />
                )}
              </div>
              <div className={`
                w-10 h-10 rounded-lg flex items-center justify-center mb-3
                ${selectedOperations.includes(option.id)
                  ? 'bg-primary-100 text-primary-600'
                  : 'bg-gray-100 text-gray-500'
                }
              `}>
                {option.icon}
              </div>
              <h4 className="font-medium text-gray-900">{option.name}</h4>
              <p className="text-sm text-gray-500 mt-1">{option.description}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Background Style Selection */}
      {selectedOperations.includes('background_replacement') && (
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">选择背景风格</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
            {backgroundStyles.map(style => (
              <button
                key={style.id}
                onClick={() => setSelectedBackground(style.id)}
                className={`
                  relative p-3 rounded-lg border-2 transition-all duration-200
                  ${selectedBackground === style.id
                    ? 'border-primary-500 ring-2 ring-primary-200'
                    : 'border-gray-200 hover:border-gray-300'
                  }
                `}
              >
                <div className={`w-full aspect-square rounded-md ${style.preview} mb-2`} />
                <p className="text-xs font-medium text-gray-900">{style.name}</p>
                <p className="text-xs text-gray-500">{style.description}</p>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Advanced Settings */}
      <div>
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
        >
          <ChevronDown className={`w-4 h-4 transition-transform ${showAdvanced ? 'rotate-180' : ''}`} />
          高级设置
        </button>

        {showAdvanced && (
          <div className="mt-4 p-4 bg-gray-50 rounded-xl space-y-4 animate-slide-up">
            {/* Strength Slider */}
            <div>
              <div className="flex justify-between mb-2">
                <label className="text-sm font-medium text-gray-700">处理强度</label>
                <span className="text-sm text-gray-500">{Math.round(strength * 100)}%</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="1"
                step="0.1"
                value={strength}
                onChange={e => setStrength(parseFloat(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>柔和</span>
                <span>强烈</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Process Button */}
      <button
        onClick={handleProcess}
        disabled={selectedOperations.length === 0 || isProcessing}
        className={`
          w-full py-4 rounded-xl font-medium text-lg transition-all duration-200
          flex items-center justify-center gap-2
          ${selectedOperations.length === 0 || isProcessing
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
            : 'bg-primary-600 hover:bg-primary-700 text-white shadow-lg hover:shadow-xl'
          }
        `}
      >
        {isProcessing ? (
          <>
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            处理中...
          </>
        ) : (
          <>
            <Wand2 className="w-5 h-5" />
            开始处理
          </>
        )}
      </button>
    </div>
  )
}
