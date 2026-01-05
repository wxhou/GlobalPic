import { useState } from 'react'
import { Download, Share2, RefreshCw, Maximize2, X, Check, ChevronLeft, ChevronRight } from 'lucide-react'

interface ResultDisplayProps {
  originalImage?: string
  resultImages: string[]
  onDownload?: (url: string) => void
  onDownloadAll?: (urls: string[]) => void
  onShare?: (url: string) => void
  onReprocess?: () => void
}

export default function ResultDisplay({
  originalImage,
  resultImages,
  onDownload,
  onDownloadAll,
  onShare,
  onReprocess
}: ResultDisplayProps) {
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [showCompare, setShowCompare] = useState(false)

  const selectedImage = resultImages[selectedIndex]

  const handleDownload = (url: string) => {
    const link = document.createElement('a')
    link.href = url
    link.download = `result-${selectedIndex + 1}.jpg`
    link.click()
    onDownload?.(url)
  }

  const handleDownloadAll = () => {
    resultImages.forEach((url, index) => {
      setTimeout(() => {
        const link = document.createElement('a')
        link.href = url
        link.download = `result-${index + 1}.jpg`
        link.click()
      }, index * 500)
    })
    onDownloadAll?.(resultImages)
  }

  const handleShare = async (url: string) => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'GlobalPic 处理结果',
          text: '查看我的AI处理图片',
          url: url
        })
      } catch (err) {
        console.log('Share cancelled')
      }
    } else {
      navigator.clipboard.writeText(url)
      alert('链接已复制到剪贴板')
    }
    onShare?.(url)
  }

  return (
    <div className="space-y-6">
      {/* Main Result Display */}
      <div className="card overflow-hidden">
        <div className="relative">
          {/* Image Container */}
          <div className="relative bg-gray-900 aspect-square max-h-[500px] flex items-center justify-center">
            {originalImage && showCompare ? (
              // Compare view
              <div className="relative w-full h-full">
                <img
                  src={originalImage}
                  alt="原图"
                  className="absolute inset-0 w-full h-full object-contain"
                />
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-1/2 h-full overflow-hidden border-r-2 border-white">
                    <img
                      src={selectedImage}
                      alt="处理后"
                      className="w-[200%] h-full object-cover object-left"
                    />
                  </div>
                </div>
                <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-black/70 text-white px-4 py-2 rounded-full text-sm">
                  滑动对比原图和处理结果
                </div>
              </div>
            ) : (
              // Single image view
              <img
                src={selectedImage}
                alt={`处理结果 ${selectedIndex + 1}`}
                className="w-full h-full object-contain"
              />
            )}

            {/* Actions Overlay */}
            <div className="absolute top-4 right-4 flex gap-2">
              <button
                onClick={() => setShowCompare(!showCompare)}
                disabled={!originalImage}
                className="p-2 bg-white/90 rounded-full hover:bg-white transition-colors disabled:opacity-50"
                title="对比查看"
              >
                <Maximize2 className="w-5 h-5 text-gray-700" />
              </button>
              <button
                onClick={() => setIsFullscreen(true)}
                className="p-2 bg-white/90 rounded-full hover:bg-white transition-colors"
                title="全屏查看"
              >
                <Maximize2 className="w-5 h-5 text-gray-700" />
              </button>
            </div>

            {/* Navigation */}
            {resultImages.length > 1 && (
              <>
                <button
                  onClick={() => setSelectedIndex(i => Math.max(0, i - 1))}
                  disabled={selectedIndex === 0}
                  className="absolute left-4 top-1/2 -translate-y-1/2 p-2 bg-white/90 rounded-full hover:bg-white transition-colors disabled:opacity-50"
                >
                  <ChevronLeft className="w-6 h-6 text-gray-700" />
                </button>
                <button
                  onClick={() => setSelectedIndex(i => Math.min(resultImages.length - 1, i + 1))}
                  disabled={selectedIndex === resultImages.length - 1}
                  className="absolute right-4 top-1/2 -translate-y-1/2 p-2 bg-white/90 rounded-full hover:bg-white transition-colors disabled:opacity-50"
                >
                  <ChevronRight className="w-6 h-6 text-gray-700" />
                </button>
              </>
            )}
          </div>

          {/* Image Counter */}
          <div className="absolute bottom-4 left-4 bg-black/70 text-white px-3 py-1 rounded-full text-sm">
            {selectedIndex + 1} / {resultImages.length}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="p-4 border-t border-gray-100">
          <div className="flex items-center justify-between">
            <div className="flex gap-3">
              <button
                onClick={() => handleDownload(selectedImage)}
                className="btn-secondary flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                下载
              </button>
              <button
                onClick={() => handleShare(selectedImage)}
                className="btn-secondary flex items-center gap-2"
              >
                <Share2 className="w-4 h-4" />
                分享
              </button>
            </div>
            
            {resultImages.length > 1 && (
              <button
                onClick={handleDownloadAll}
                className="btn-primary flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                批量下载
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Thumbnail Grid */}
      {resultImages.length > 1 && (
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-3">所有结果</h3>
          <div className="grid grid-cols-4 gap-3">
            {resultImages.map((url, index) => (
              <button
                key={index}
                onClick={() => setSelectedIndex(index)}
                className={`
                  relative aspect-square rounded-lg overflow-hidden border-2 transition-all
                  ${selectedIndex === index
                    ? 'border-primary-500 ring-2 ring-primary-200'
                    : 'border-transparent hover:border-gray-300'
                  }
                `}
              >
                <img
                  src={url}
                  alt={`结果 ${index + 1}`}
                  className="w-full h-full object-cover"
                />
                {selectedIndex === index && (
                  <div className="absolute top-2 right-2 w-6 h-6 bg-primary-500 rounded-full flex items-center justify-center">
                    <Check className="w-4 h-4 text-white" />
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Reprocess Button */}
      {onReprocess && (
        <div className="flex justify-center">
          <button
            onClick={onReprocess}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            重新处理
          </button>
        </div>
      )}

      {/* Fullscreen Modal */}
      {isFullscreen && (
        <div className="fixed inset-0 bg-black z-50 flex items-center justify-center">
          <button
            onClick={() => setIsFullscreen(false)}
            className="absolute top-4 right-4 p-2 text-white hover:bg-white/20 rounded-full transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
          <img
            src={selectedImage}
            alt="全屏查看"
            className="max-w-full max-h-full object-contain"
          />
        </div>
      )}
    </div>
  )
}
