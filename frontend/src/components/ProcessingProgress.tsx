import { useEffect, useState } from 'react'
import { Clock, X, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'

interface ProcessingProgressProps {
  jobId: number
  onCancel?: () => void
  onComplete?: (result: ProcessingResult) => void
  onError?: (error: string) => void
}

interface ProcessingResult {
  output_urls: string[]
}

interface JobStatus {
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  result_urls?: string[]
  error_message?: string
  estimated_completion?: string
  started_at?: string
  completed_at?: string
}

const processingSteps = [
  { progress: 10, message: '正在分析图片...' },
  { progress: 25, message: '正在检测文字...' },
  { progress: 50, message: '正在分割主体...' },
  { progress: 75, message: '正在生成背景...' },
  { progress: 90, message: '正在优化图片...' },
  { progress: 100, message: '处理完成' }
]

export default function ProcessingProgress({
  jobId,
  onCancel,
  onComplete,
  onError
}: ProcessingProgressProps) {
  const [status, setStatus] = useState<JobStatus>({
    status: 'pending',
    progress: 0
  })
  const [currentStep, setCurrentStep] = useState(0)
  const [elapsedTime, setElapsedTime] = useState(0)

  // Simulate progress (in real app, this would be from WebSocket or polling)
  useEffect(() => {
    if (status.status === 'processing') {
      const interval = setInterval(() => {
        setStatus(prev => {
          if (prev.progress >= 100) {
            clearInterval(interval)
            return { ...prev, status: 'completed' }
          }
          return { ...prev, progress: prev.progress + 5 }
        })
        setElapsedTime(t => t + 1)
      }, 1000)
      return () => clearInterval(interval)
    }
  }, [status.status])

  // Update current step based on progress
  useEffect(() => {
    const stepIndex = processingSteps.findIndex(
      step => status.progress >= step.progress
    )
    setCurrentStep(Math.max(0, stepIndex))
  }, [status.progress])

  // Handle completion
  useEffect(() => {
    if (status.status === 'completed' && status.result_urls) {
      onComplete?.({ output_urls: status.result_urls })
    }
    if (status.status === 'failed') {
      onError?.(status.error_message || '处理失败')
    }
  }, [status.status])

  // Calculate estimated time
  const getEstimatedTime = () => {
    const remainingProgress = 100 - status.progress
    const secondsPerPercent = elapsedTime / (status.progress || 1)
    const estimatedSeconds = Math.ceil(remainingProgress * secondsPerPercent)
    
    if (estimatedSeconds < 60) {
      return `约 ${estimatedSeconds} 秒`
    }
    return `约 ${Math.ceil(estimatedSeconds / 60)} 分钟`
  }

  return (
    <div className="card p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className={`
            w-10 h-10 rounded-full flex items-center justify-center
            ${status.status === 'processing' ? 'bg-primary-100' : ''}
            ${status.status === 'completed' ? 'bg-green-100' : ''}
            ${status.status === 'failed' ? 'bg-red-100' : ''}
          `}>
            {status.status === 'processing' && (
              <Loader2 className="w-5 h-5 text-primary-600 animate-spin" />
            )}
            {status.status === 'completed' && (
              <CheckCircle className="w-5 h-5 text-green-600" />
            )}
            {status.status === 'failed' && (
              <AlertCircle className="w-5 h-5 text-red-600" />
            )}
          </div>
          <div>
            <h3 className="font-medium text-gray-900">
              {status.status === 'processing' && '处理中...'}
              {status.status === 'completed' && '处理完成'}
              {status.status === 'failed' && '处理失败'}
              {status.status === 'pending' && '等待处理'}
            </h3>
            <p className="text-sm text-gray-500">
              {status.status === 'processing' && `预计剩余时间: ${getEstimatedTime()}`}
              {status.status === 'completed' && '图片已生成完成'}
              {status.status === 'failed' && status.error_message}
            </p>
          </div>
        </div>
        
        {status.status === 'processing' && onCancel && (
          <button
            onClick={onCancel}
            className="p-2 text-gray-400 hover:text-red-500 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex justify-between text-sm mb-2">
          <span className="text-gray-600">处理进度</span>
          <span className="font-medium text-gray-900">{status.progress}%</span>
        </div>
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`
              h-full rounded-full transition-all duration-500
              ${status.status === 'failed' ? 'bg-red-500' : 'bg-primary-500'}
            `}
            style={{ width: `${status.progress}%` }}
          />
        </div>
      </div>

      {/* Processing Steps */}
      {status.status === 'processing' && (
        <div className="space-y-3">
          {processingSteps.map((step, index) => (
            <div
              key={index}
              className={`
                flex items-center gap-3 p-3 rounded-lg transition-all duration-300
                ${index <= currentStep
                  ? 'bg-primary-50'
                  : 'bg-gray-50 opacity-50'
                }
              `}
            >
              <div className={`
                w-6 h-6 rounded-full flex items-center justify-center text-sm
                ${index < currentStep
                  ? 'bg-primary-500 text-white'
                  : index === currentStep
                    ? 'bg-primary-100 text-primary-600 animate-pulse'
                    : 'bg-gray-200 text-gray-500'
                }
              `}>
                {index < currentStep ? (
                  <CheckCircle className="w-4 h-4" />
                ) : (
                  index + 1
                )}
              </div>
              <span className={`
                text-sm
                ${index <= currentStep ? 'text-gray-900' : 'text-gray-500'}
              `}>
                {step.message}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Elapsed Time */}
      {status.status === 'processing' && (
        <div className="flex items-center gap-2 mt-6 pt-4 border-t border-gray-100">
          <Clock className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-500">
            已处理 {elapsedTime} 秒
          </span>
        </div>
      )}

      {/* Completion */}
      {status.status === 'completed' && (
        <div className="mt-4 p-4 bg-green-50 rounded-lg">
          <p className="text-sm text-green-700">
            ✅ 处理完成！共生成 {status.result_urls?.length || 0} 张图片
          </p>
        </div>
      )}

      {/* Error */}
      {status.status === 'failed' && (
        <div className="mt-4 p-4 bg-red-50 rounded-lg">
          <p className="text-sm text-red-700">
            ❌ {status.error_message || '处理过程中发生错误，请稍后重试'}
          </p>
        </div>
      )}
    </div>
  )
}
