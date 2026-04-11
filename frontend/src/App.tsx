
import ResumeScanner from './components/ResumeScanner.tsx'
import './App.css'

function App() {
  return (
    <div className="min-h-screen bg-gray-900 text-white font-sans">
      {/* Header */}
      <header className="p-6 border-b border-gray-800">
        <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
          Resume AI Scanner
        </h1>
      </header>

      <main className="container mx-auto py-10 px-4">
        {/* Day 3 Core Logic Component */}
        <ResumeScanner />
      </main>

      <footer className="py-6 text-center text-gray-500 text-sm">
        Day 3: Integration Mode • Powered by Groq & FastAPI
      </footer>
    </div>
  )
}

export default App