import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, X, Image as ImageIcon, CheckCircle, AlertCircle } from 'lucide-react'

interface UploadedFile {
  file: File
  preview: string
  status: 'pending' | 'uploading' | 'success' | 'error'
  progress: number
}

interface ImageUploadProps {
  onUploadComplete?: (files: UploadedFile[]) => void
  maxFiles?: number
  maxSize?: number // in bytes
}

export default function ImageUpload({
  onUploadComplete,
  maxFiles = 9,
  maxSize = 20 * 1024 * 1024 // 20MB
}: ImageUploadProps) {
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [isUploading, setIsUploading] = useState(false)

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map(file => ({
      file,
      preview: URL.createObjectURL(file),
      status: 'pending' as const,
      progress: 0
    }))
    setFiles(prev => [...prev, ...newFiles].slice(0, maxFiles))
  }, [maxFiles])

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    maxFiles: maxFiles - files.length,
    maxSize,
    accept: {
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'image/webp': ['.webp']
    }
  })

  const removeFile = (index: number) => {
    setFiles(prev => {
      const newFiles = [...prev]
      URL.revokeObjectURL(newFiles[index].preview)
      newFiles.splice(index, 1)
      return newFiles
    })
  }

  const uploadFiles = async () => {
    setIsUploading(true)
    
    for (let i = 0; i < files.length; i++) {
      if (files[i].status === 'pending') {
        setFiles(prev => {
          const newFiles = [...prev]
          newFiles[i].status = 'uploading'
          return newFiles
        })

        // 模拟上传进度 (实际应用中应使用真实的进度回调)
        // TODO: 替换为实际的 API 上传逻辑，支持进度回调
        // const response = await uploadApi.uploadWithProgress(file, (progress) => {...})
        for (let progress = 0; progress <= 100; progress += 10) {
          await new Promise(resolve => setTimeout(resolve, 100))
          setFiles(prev => {
            const newFiles = [...prev]
            if (newFiles[i].status === 'uploading') {
              newFiles[i].progress = progress
            }
            return newFiles
          })
        }

        // Simulate upload success
        setFiles(prev => {
          const newFiles = [...prev]
          newFiles[i].status = 'success'
          newFiles[i].progress = 100
          return newFiles
        })
      }
    }

    setIsUploading(false)
    onUploadComplete?.(files.filter(f => f.status === 'success'))
  }

  return (
    <div className="space-y-4">
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200
          ${isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'}
          ${isDragReject ? 'border-red-500 bg-red-50' : ''}
        `}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-4">
          <div className={`p-4 rounded-full ${isDragActive ? 'bg-primary-100' : 'bg-gray-100'}`}>
            <Upload className={`w-8 h-8 ${isDragActive ? 'text-primary-600' : 'text-gray-400'}`} />
          </div>
          <div>
            <p className="text-lg font-medium text-gray-900">
              {isDragActive ? '释放以上传图片' : '拖拽图片到此处，或点击选择'}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              支持 JPG、PNG、WEBP 格式，单文件最大 20MB，最多 {maxFiles} 张
            </p>
          </div>
        </div>
      </div>

      {/* Preview Grid */}
      {files.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
          {files.map((uploadFile, index) => (
            <div
              key={index}
              className="relative group card overflow-hidden"
            >
              <div className="aspect-square">
                <img
                  src={uploadFile.preview}
                  alt={uploadFile.file.name}
                  className="w-full h-full object-cover"
                />
              </div>
              
              {/* Status overlay */}
              <div className="absolute inset-0 bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={() => removeFile(index)}
                  className="p-2 bg-white/20 rounded-full hover:bg-white/40 transition-colors"
                >
                  <X className="w-5 h-5 text-white" />
                </button>
              </div>

              {/* Status badge */}
              <div className="absolute top-2 right-2">
                {uploadFile.status === 'success' && (
                  <div className="p-1 bg-green-500 rounded-full">
                    <CheckCircle className="w-4 h-4 text-white" />
                  </div>
                )}
                {uploadFile.status === 'error' && (
                  <div className="p-1 bg-red-500 rounded-full">
                    <AlertCircle className="w-4 h-4 text-white" />
                  </div>
                )}
                {uploadFile.status === 'uploading' && (
                  <div className="p-1 bg-blue-500 rounded-full">
                    <Upload className="w-4 h-4 text-white animate-spin" />
                  </div>
                )}
              </div>

              {/* Progress bar */}
              {uploadFile.status === 'uploading' && (
                <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-200">
                  <div
                    className="h-full bg-primary-500 transition-all duration-200"
                    style={{ width: `${uploadFile.progress}%` }}
                  />
                </div>
              )}

              {/* File name */}
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-2">
                <p className="text-xs text-white truncate">{uploadFile.file.name}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Upload button */}
      {files.length > 0 && files.some(f => f.status === 'pending') && (
        <div className="flex justify-end gap-4">
          <button
            onClick={() => {
              files.forEach((_, index) => removeFile(index))
            }}
            className="btn-secondary"
          >
            清除全部
          </button>
          <button
            onClick={uploadFiles}
            disabled={isUploading}
            className="btn-primary"
          >
            {isUploading ? '上传中...' : `上传 ${files.filter(f => f.status === 'pending').length} 张图片`}
          </button>
        </div>
      )}
    </div>
  )
}
