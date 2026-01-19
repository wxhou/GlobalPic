import { useState } from 'react'
import { Check, Sparkles, Zap, Crown, CreditCard, Loader2 } from 'lucide-react'

interface SubscriptionPlanProps {
  currentPlan?: string
  onSelectPlan?: (planId: string) => void
}

const plans = [
  {
    id: 'free',
    name: '免费版',
    price: { monthly: 0, yearly: 0 },
    icon: Zap,
    color: 'gray',
    features: [
      '3张图片免费试用',
      '低分辨率输出',
      '基础处理功能',
      '社区支持'
    ],
    notIncluded: [
      '高清输出',
      '批量处理',
      'API访问',
      '优先支持'
    ]
  },
  {
    id: 'personal',
    name: '个人版',
    price: { monthly: 19, yearly: 190 },
    icon: Sparkles,
    color: 'primary',
    popular: true,
    features: [
      '无限图像处理',
      '高清输出 (4K)',
      '所有处理功能',
      '智能文案生成',
      '邮件支持'
    ],
    notIncluded: [
      'API访问',
      '团队协作'
    ]
  },
  {
    id: 'enterprise',
    name: '企业版',
    price: { monthly: 99, yearly: 990 },
    icon: Crown,
    color: 'amber',
    features: [
      '无限图像处理',
      '超高清输出 (4K)',
      '完整功能套件',
      'API访问权限',
      '团队协作',
      '专属客服',
      '优先处理'
    ],
    notIncluded: []
  }
]

const creditPackages = [
  { credits: 10, price: 4.99, name: '10张体验包' },
  { credits: 50, price: 19.99, name: '50张经济包' },
  { credits: 100, price: 34.99, name: '100张超值包' }
]

export default function SubscriptionPlan({ currentPlan = 'free', onSelectPlan }: SubscriptionPlanProps) {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly')
  const [activeTab, setActiveTab] = useState<'subscription' | 'credits'>('subscription')
  const [loading, setLoading] = useState<string | null>(null)

  const handleSelectPlan = async (planId: string) => {
    if (planId === currentPlan) return

    setLoading(planId)

    if (onSelectPlan) {
      onSelectPlan(planId)
    }
    setLoading(null)
  }

  const handleBuyCredits = async (packageIndex: number) => {
    setLoading(`credit_${packageIndex}`)
    // TODO: 集成实际的 API 调用
    console.debug('购买额度包:', packageIndex)
    setLoading(null)
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-100">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-amber-100 rounded-xl flex items-center justify-center">
            <CreditCard className="w-5 h-5 text-amber-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">订阅套餐</h3>
            <p className="text-sm text-gray-500">选择适合您的方案</p>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex gap-2 mt-4">
          <button
            onClick={() => setActiveTab('subscription')}
            className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'subscription'
                ? 'bg-gray-900 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            订阅套餐
          </button>
          <button
            onClick={() => setActiveTab('credits')}
            className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'credits'
                ? 'bg-gray-900 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            按需购买
          </button>
        </div>
      </div>

      {activeTab === 'subscription' ? (
        <>
          {/* Billing Cycle Toggle */}
          <div className="px-6 py-4 border-b border-gray-100">
            <div className="flex items-center justify-center gap-3">
              <span className={`text-sm ${billingCycle === 'monthly' ? 'text-gray-900' : 'text-gray-500'}`}>
                月付
              </span>
              <button
                onClick={() => setBillingCycle(billingCycle === 'monthly' ? 'yearly' : 'monthly')}
                className={`
                  relative w-14 h-7 rounded-full transition-colors
                  ${billingCycle === 'yearly' ? 'bg-primary-600' : 'bg-gray-300'}
                `}
              >
                <span className={`
                  absolute top-1 w-5 h-5 bg-white rounded-full shadow transition-transform
                  ${billingCycle === 'yearly' ? 'left-8' : 'left-1'}
                `} />
              </button>
              <span className={`text-sm ${billingCycle === 'yearly' ? 'text-gray-900' : 'text-gray-500'}`}>
                年付 <span className="text-green-600 text-xs">(省2个月)</span>
              </span>
            </div>
          </div>

          {/* Plans */}
          <div className="p-6 grid gap-4 md:grid-cols-3">
            {plans.map(plan => {
              const Icon = plan.icon
              const isCurrent = currentPlan === plan.id
              const price = billingCycle === 'monthly' ? plan.price.monthly : plan.price.yearly

              return (
                <div
                  key={plan.id}
                  className={`
                    relative rounded-xl border-2 p-4 transition-all
                    ${isCurrent
                      ? 'border-gray-900 bg-gray-50'
                      : 'border-gray-200 hover:border-gray-300'
                    }
                    ${plan.popular ? 'ring-2 ring-primary-500 ring-offset-2' : ''}
                  `}
                >
                  {plan.popular && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary-600 text-white text-xs px-3 py-1 rounded-full">
                      最受欢迎
                    </div>
                  )}

                  <div className="flex items-center gap-2 mb-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                      plan.color === 'primary' ? 'bg-primary-100' :
                      plan.color === 'amber' ? 'bg-amber-100' :
                      'bg-gray-100'
                    }`}>
                      <Icon className={`w-4 h-4 ${
                        plan.color === 'primary' ? 'text-primary-600' :
                        plan.color === 'amber' ? 'text-amber-600' :
                        'text-gray-600'
                      }`} />
                    </div>
                    <span className="font-medium text-gray-900">{plan.name}</span>
                    {isCurrent && (
                      <span className="ml-auto text-xs bg-gray-200 px-2 py-0.5 rounded text-gray-600">
                        当前
                      </span>
                    )}
                  </div>

                  <div className="mb-4">
                    <span className="text-2xl font-bold text-gray-900">${price}</span>
                    <span className="text-gray-500 text-sm">/{billingCycle === 'monthly' ? '月' : '年'}</span>
                  </div>

                  <ul className="space-y-2 mb-4">
                    {plan.features.map((feature, idx) => (
                      <li key={idx} className="flex items-center gap-2 text-sm text-gray-600">
                        <Check className="w-4 h-4 text-green-500 flex-shrink-0" />
                        {feature}
                      </li>
                    ))}
                    {plan.notIncluded.map((feature, idx) => (
                      <li key={idx} className="flex items-center gap-2 text-sm text-gray-400">
                        <span className="w-4 h-4 text-gray-300 flex-shrink-0">×</span>
                        {feature}
                      </li>
                    ))}
                  </ul>

                  <button
                    onClick={() => handleSelectPlan(plan.id)}
                    disabled={isCurrent || loading === plan.id}
                    className={`
                      w-full py-2 rounded-lg text-sm font-medium transition-all
                      ${isCurrent
                        ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                        : plan.popular
                          ? 'bg-primary-600 hover:bg-primary-700 text-white'
                          : 'bg-gray-900 hover:bg-gray-800 text-white'
                      }
                      ${loading === plan.id ? 'opacity-75' : ''}
                    `}
                  >
                    {loading === plan.id ? (
                      <Loader2 className="w-4 h-4 animate-spin mx-auto" />
                    ) : isCurrent ? (
                      '当前套餐'
                    ) : (
                      `升级到${plan.name}`
                    )}
                  </button>
                </div>
              )
            })}
          </div>
        </>
      ) : (
        /* Credit Packages */
        <div className="p-6">
          <p className="text-sm text-gray-500 mb-4">按需购买处理额度，永不过期</p>
          <div className="grid gap-4 md:grid-cols-3">
            {creditPackages.map((pkg, idx) => (
              <div
                key={idx}
                className="relative rounded-xl border border-gray-200 p-4 text-center hover:border-gray-300 transition-colors"
              >
                <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                  <CreditCard className="w-6 h-6 text-blue-600" />
                </div>
                <h4 className="font-medium text-gray-900">{pkg.name}</h4>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  ${pkg.price}
                </p>
                <p className="text-sm text-gray-500 mb-4">
                  约 ${(pkg.price / pkg.credits).toFixed(2)}/张
                </p>
                <button
                  onClick={() => handleBuyCredits(idx)}
                  disabled={loading === `credit_${idx}`}
                  className={`
                    w-full py-2 rounded-lg text-sm font-medium transition-all
                    bg-blue-600 hover:bg-blue-700 text-white
                    ${loading === `credit_${idx}` ? 'opacity-75' : ''}
                  `}
                >
                  {loading === `credit_${idx}` ? (
                    <Loader2 className="w-4 h-4 animate-spin mx-auto" />
                  ) : (
                    '立即购买'
                  )}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
