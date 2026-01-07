import { useState, useCallback } from 'react'
import { Upload, X, Layers, Loader2, Download, Trash2, CheckCircle, AlertCircle } from 'lucide-react'
import { batchApi, BatchCreateRequest } from '../api/batch'

interface BatchImage {
  id: string
  file: File
  preview: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  error?: string
}

interface BatchProcessorProps {
  onProcess?: (taskId: string) => void
}

export default function BatchProcessor({ onProcess }: BatchProcessorProps) {
  const [images, setImages] = useState<BatchImage[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [selectedOperations, setSelectedOperations] = useState<string[]>(['text_removal', 'background_replacement'])
  const [selectedStyle, setSelectedStyle] = useState('minimal_white')
  const [error, setError] = useState<string | null>(null)
  const [taskId, setTaskId] = useState<string | null>(null)

  // 将文件转换为 base64
  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.readAsDataURL(file)
      reader.onload = () => resolve(reader.result as string)
      reader.onerror = error => reject(error)
    })
  }

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()

    const files = Array.from(e.dataTransfer.files).filter(
      file => file.type.startsWith('image/')
    )

    await addImages(files)
  }, [])

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    await addImages(files)
  }

  const addImages = async (files: File[]) => {
    const newImages: BatchImage[] = []
    for (const file of files.slice(0, 50 - images.length)) {
      newImages.push({
        id: Math.random().toString(36).substr(2, 9),
        file,
        preview: URL.createObjectURL(file),
        status: 'pending'
      })
    }
    setImages(prev => [...prev, ...newImages].slice(0, 50))
  }

  const removeImage = (id: string) => {
    setImages(prev => {
      const image = prev.find(img => img.id === id)
      if (image) {
        URL.revokeObjectURL(image.preview)
      }
      return prev.filter(img => img.id !== id)
    })
  }

  const toggleOperation = (op: string) => {
    setSelectedOperations(prev =>
      prev.includes(op)
        ? prev.filter(o => o !== op)
        : [...prev, op]
    )
  }

  const handleProcess = async () => {
    if (images.length === 0 || selectedOperations.length === 0) {
      setError('请选择至少一张图片和一个处理操作')
      return
    }

    setIsProcessing(true)
    setProgress(0)
    setError(null)

    try {
      // 转换图片为 base64
      const imageDataList = await Promise.all(
        images.map(async (img) => ({
          image: await fileToBase64(img.file),
          filename: img.file.name
        }))
      )

      // 创建批量任务
      const request: BatchCreateRequest = {
        images: imageDataList,
        operations: selectedOperations,
        style_id: selectedStyle
      }

      const response = await batchApi.create(request)
      setTaskId(response.data.task_id)

      // 轮询任务状态
      await pollTaskStatus(response.data.task_id)

      setImages(prev => prev.map(img => ({ ...img, status: 'completed' as const })))
      setProgress(100)

      if (onProcess) {
        onProcess(response.data.task_id)
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : '处理失败，请重试'
      setError(errorMessage)
      setImages(prev => prev.map(img => ({ ...img, status: 'failed' as const, error: errorMessage })))
    } finally {
      setIsProcessing(false)
    }
  }

  const pollTaskStatus = async (id: string) => {
    const maxAttempts = 120 // 最多轮询 2 分钟
    let attempts = 0

    const poll = async () => {
      if (attempts >= maxAttempts) {
        throw new Error('处理超时')
      }

      try {
        const response = await batchApi.getStatus(id)
        const status = response.data

        // 更新进度
        const newProgress = status.progress
        setProgress(newProgress)

        // 更新各图片状态
        setImages(prev => {
          const processedCount = Math.floor((newProgress / 100) * prev.length)
          return prev.map((img, idx) => {
            if (idx < processedCount) {
              return { ...img, status: 'completed' as const }
            } else if (idx === processedCount) {
              return { ...img, status: 'processing' as const }
            }
            return img
          })
        })

        if (status.status === 'completed') {
          return true
        } else if (status.status === 'failed') {
          throw new Error('批量处理任务失败')
        }
      } catch {
        // 继续轮询
      }

      attempts++
      await new Promise(resolve => setTimeout(resolve, 1000))
      return poll()
    }

    return poll()
  }

  const handleDownload = async () => {
    if (!taskId) {
      setError('没有可下载的结果')
      return
    }

    try {
      const response = await batchApi.download(taskId)
      // 创建下载链接
      const link = document.createElement('a')
      link.href = response.data.download_url
      link.download = `batch_${taskId}.zip`
      link.click()
    } catch {
      setError('下载失败，请稍后重试')
    }
  }

  const handleClear = () => {
    images.forEach(img => URL.revokeObjectURL(img.preview))
    setImages([])
    setProgress(0)
    setTaskId(null)
    setError(null)
  }

  const operations = [
    { id: 'text_removal', name: '文字抹除' },
    { id: 'background_replacement', name: '背景重绘' }
  ]

  const styles = [
    { id: 'minimal_white', name: '极简白', preview: 'bg-white' },
    { id: 'modern_home', name: '现代家居', preview: 'bg-amber-100' },
    { id: 'amazon_standard', name: '亚马逊标准', preview: 'bg-white' },
    { id: 'tiktok_vibrant', name: 'TikTok风格', preview: 'bg-gradient-to-r from-pink-500 to-purple-500' }
  ]

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-100">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
            <Layers className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">批量处理</h3>
            <p className="text-sm text-gray-500">一次最多处理50张图片</p>
          </div>
          {images.length > 0 && (
            <button
              onClick={handleClear}
              className="ml-auto text-sm text-red-500 hover:text-red-600 flex items-center gap-1"
            >
              <Trash2 className="w-4 h-4" />
              清空
            </button>
          )}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mx-6 mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-600">
          <AlertCircle className="w-5 h-5" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      {/* Upload Area */}
      <div className="p-6">
        <div
          onDrop={handleDrop}
          onDragOver={e => e.preventDefault()}
          onDragEnter={e => e.preventDefault()}
          className={`
            relative border-2 border-dashed rounded-xl p-8 text-center transition-colors
            ${isProcessing
              ? 'border-gray-200 bg-gray-50'
              : 'border-gray-300 hover:border-primary-400 hover:bg-primary-50'
            }
          `}
        >
          <input
            type="file"
            multiple
            accept="image/*"
            onChange={handleFileSelect}
            disabled={isProcessing}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />

          <Upload className={`w-12 h-12 mx-auto mb-3 ${isProcessing ? 'text-gray-300' : 'text-gray-400'}`} />
          <p className="text-gray-600 font-medium">
            {isProcessing ? '处理中...' : '拖拽图片到此处，或点击上传'}
          </p>
          <p className="text-sm text-gray-400 mt-1">
            支持 JPG、PNG、WEBP，单张最大20MB
          </p>

          {/* Progress Bar */}
          {isProcessing && (
            <div className="mt-4">
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary-600 transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-sm text-gray-500 mt-2">
                {Math.round(progress)}% - 正在处理 {images.length} 张图片
              </p>
            </div>
          )}
        </div>

        {/* Image Preview Grid */}
        {images.length > 0 && (
          <div className="mt-4">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-gray-500">
                已选择 {images.length} 张图片
              </p>
            </div>

            <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 gap-2 max-h-48 overflow-y-auto">
              {images.map((image, idx) => (
                <div
                  key={image.id}
                  className="relative group aspect-square rounded-lg overflow-hidden bg-gray-100"
                >
                  <img
                    src={image.preview}
                    alt={`预览 ${idx + 1}`}
                    className="w-full h-full object-cover"
                  />

                  {/* Status Overlay */}
                  <div className="absolute inset-0 bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                    {image.status === 'completed' && (
                      <CheckCircle className="w-6 h-6 text-green-400" />
                    )}
                    {image.status === 'processing' && (
                      <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />
                    )}
                    {image.status === 'failed' && (
                      <AlertCircle className="w-6 h-6 text-red-400" />
                    )}
                  </div>

                  {/* Remove Button */}
                  {!isProcessing && (
                    <button
                      onClick={() => removeImage(image.id)}
                      className="absolute top-1 right-1 w-5 h-5 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  )}

                  {/* Index */}
                  <div className="absolute bottom-1 left-1 px-1 bg-black/60 text-white text-xs rounded">
                    {idx + 1}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Options */}
      {images.length > 0 && !isProcessing && (
        <div className="px-6 py-4 border-t border-gray-100">
          {/* Operations */}
          <div className="mb-4">
            <p className="text-sm font-medium text-gray-700 mb-2">选择处理操作</p>
            <div className="flex flex-wrap gap-2">
              {operations.map(op => (
                <button
                  key={op.id}
                  onClick={() => toggleOperation(op.id)}
                  className={`
                    px-3 py-1.5 rounded-lg text-sm font-medium transition-all
                    ${selectedOperations.includes(op.id)
                      ? 'bg-primary-100 text-primary-700 border-2 border-primary-300'
                      : 'bg-gray-100 text-gray-600 border-2 border-transparent hover:bg-gray-200'
                    }
                  `}
                >
                  {op.name}
                </button>
              ))}
            </div>
          </div>

          {/* Style */}
          <div className="mb-4">
            <p className="text-sm font-medium text-gray-700 mb-2">背景风格</p>
            <div className="flex flex-wrap gap-2">
              {styles.map(style => (
                <button
                  key={style.id}
                  onClick={() => setSelectedStyle(style.id)}
                  className={`
                    px-3 py-1.5 rounded-lg text-sm font-medium transition-all flex items-center gap-2
                    ${selectedStyle === style.id
                      ? 'bg-gray-900 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }
                  `}
                >
                  <span className={`w-4 h-4 rounded ${style.preview} border border-gray-300`} />
                  {style.name}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      {images.length > 0 && (
        <div className="px-6 py-4 border-t border-gray-100 flex gap-3">
          <button
            onClick={handleProcess}
            disabled={isProcessing || selectedOperations.length === 0}
            className={`
              flex-1 py-3 rounded-xl font-medium transition-all flex items-center justify-center gap-2
              ${isProcessing || selectedOperations.length === 0
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-primary-600 hover:bg-primary-700 text-white shadow-lg'
              }
            `}
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                处理中...
              </>
            ) : (
              <>
                <Layers className="w-5 h-5" />
                开始批量处理
              </>
            )}
          </button>

          {taskId && images.some(img => img.status === 'completed') && (
            <button
              onClick={handleDownload}
              className="px-6 py-3 rounded-xl font-medium bg-green-600 hover:bg-green-700 text-white flex items-center gap-2"
            >
              <Download className="w-5 h-5" />
              下载结果
            </button>
          )}
        </div>
      )}
    </div>
  )
}
