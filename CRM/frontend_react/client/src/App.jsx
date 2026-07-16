import { useState } from 'react'
// import reactLogo from './assets/react.svg'
// import viteLogo from './assets/vite.svg'
// import heroImg from './assets/hero.png'
import Navbar from './pages/Navbar'
import './App.css'
import Dashboard from './pages/Dashboard'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="h-screen flex flex-col">

    <Navbar />
    <Dashboard />
    </div>
  )
}

export default App;
