import { useAuth } from '../context/AuthContext'
import { Upload, Image, Settings, LogOut, Wand2 } from 'lucide-react'

export default function Dashboard() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">GlobalPic</h1>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                  <span className="text-primary-600 font-medium">
                    {user?.name?.charAt(0).toUpperCase() || 'U'}
                  </span>
                </div>
                <span className="text-sm text-gray-700">{user?.name || user?.email}</span>
              </div>
              <button
                onClick={logout}
                className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                title="退出登录"
              >
                <LogOut size={20} />
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* 上传卡片 */}
          <div className="card p-6 hover:shadow-md transition-shadow cursor-pointer group">
            <div className="flex items-center gap-4 mb-4">
              <div className="p-3 bg-primary-100 rounded-lg group-hover:bg-primary-200 transition-colors">
                <Upload className="w-6 h-6 text-primary-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">上传图片</h3>
            </div>
            <p className="text-gray-600 text-sm">
              拖拽或点击上传图片，支持JPG、PNG、WEBP格式，单文件最大20MB
            </p>
          </div>

          {/* 我的图片卡片 */}
          <div className="card p-6 hover:shadow-md transition-shadow cursor-pointer group">
            <div className="flex items-center gap-4 mb-4">
              <div className="p-3 bg-green-100 rounded-lg group-hover:bg-green-200 transition-colors">
                <Image className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">我的图片</h3>
            </div>
            <p className="text-gray-600 text-sm">
              查看和管理已上传的图片，处理历史记录
            </p>
          </div>

          {/* AI处理卡片 */}
          <div className="card p-6 hover:shadow-md transition-shadow cursor-pointer group">
            <div className="flex items-center gap-4 mb-4">
              <div className="p-3 bg-purple-100 rounded-lg group-hover:bg-purple-200 transition-colors">
                <Wand2 className="w-6 h-6 text-purple-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">AI处理</h3>
            </div>
            <p className="text-gray-600 text-sm">
              智能去文字、背景重绘、主体分割，一键生成专业级产品图
            </p>
          </div>
        </div>

        {/* 快捷处理区域 */}
        <div className="mt-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">快捷处理</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { name: '智能去文字', description: '自动检测并移除水印', icon: '📝' },
              { name: '背景重绘', description: '欧美风格背景生成', icon: '🎨' },
              { name: '主体分割', description: '精确提取产品主体', icon: '✂️' },
              { name: '尺寸适配', description: '多平台尺寸一键调整', icon: '📐' },
            ].map((item, index) => (
              <div
                key={index}
                className="card p-4 hover:shadow-md transition-all cursor-pointer hover:-translate-y-1"
              >
                <div className="text-2xl mb-2">{item.icon}</div>
                <h3 className="font-medium text-gray-900">{item.name}</h3>
                <p className="text-sm text-gray-500">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  )
}
