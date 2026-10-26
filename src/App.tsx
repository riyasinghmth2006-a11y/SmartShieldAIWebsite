import { useEffect, useState } from 'react'
import { AppFrame, Background, Footer, TopNav, type Page } from './components/Shell'
import Home from './pages/Home'
import Scam from './pages/Scam'
import News from './pages/News'
import Deepfake from './pages/Deepfake'
import { About, How } from './pages/Info'

export default function App() {
  const [page, setPage] = useState<Page>('home')
  const go = (p: Page) => {
    setPage(p)
    window.scrollTo({ top: 0 })
  }
  useEffect(() => {
    document.title = 'SmartShield AI — Your Digital Safety Companion'
  }, [])

  return (
    <div className="relative min-h-screen overflow-x-hidden bg-bg font-sans text-ink">
      <Background />
      {page === 'home' ? (
        <>
          <TopNav page={page} go={go} />
          <Home go={go} />
          <Footer go={go} />
        </>
      ) : (
        <AppFrame page={page} go={go}>
          {page === 'scam' && <Scam />}
          {page === 'news' && <News />}
          {page === 'deepfake' && <Deepfake />}
          {page === 'how' && <How />}
          {page === 'about' && <About go={go} />}
        </AppFrame>
      )}
    </div>
  )
}
