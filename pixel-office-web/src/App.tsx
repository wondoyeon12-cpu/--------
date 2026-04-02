import { useEffect, useState } from 'react';
import './index.css';

type AgentData = {
  status: string;
  task: string;
};

type AgentStatus = {
  [key: string]: AgentData;
};

function App() {
  const [agents, setAgents] = useState<AgentStatus>({});

  useEffect(() => {
    // 1초 단위로 파이썬 서버에서 JSON 폴링
    const fetchStatus = async () => {
      try {
        const res = await fetch('http://127.0.0.1:8000/api/status');
        const data = await res.json();
        setAgents(data);
      } catch (err) {
        console.error("데이터 연동 에러:", err);
      }
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex h-screen w-screen overflow-hidden">
      {/* 1. Main Canvas Area */}
      <div className="flex-1 relative flex flex-col items-center justify-center bg-[#07070f]">
        {/* 상단 Header */}
        <div className="absolute top-0 w-full h-16 glass-panel flex items-center justify-between px-8 z-10">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-md bg-indigo-500 flex items-center justify-center font-bold text-xl">P</div>
            <h1 className="text-lg font-bold text-gray-100 mt-1">Pixel AI 빌더 (프리미엄 랩스)</h1>
          </div>
          <div className="flex items-center gap-4 text-sm font-semibold text-gray-300">
            <span className="bg-green-500/20 text-green-400 px-3 py-1.5 rounded-full border border-green-500/30">
              🟢 시스템 정상 가동 중
            </span>
          </div>
        </div>

        {/* 오피스 렌더링 컨테이너 */}
        <div className="relative w-full max-w-[1000px] aspect-video border-[4px] border-[#222233] rounded-xl overflow-hidden shadow-2xl shadow-indigo-500/20 mt-10">
          {/* 픽셀 배경 이미지 */}
          <img src="/assets/office_bg.png" alt="Office BG" className="absolute inset-0 w-full h-full object-cover opacity-90" />
          
          {/* 에이전트 캐릭터들 배치 */}
          {Object.entries(agents).map(([name, data], idx) => {
             const positions = [
               { left: '20%', top: '40%' },
               { left: '40%', top: '40%' },
               { left: '60%', top: '40%' },
               { left: '40%', top: '70%' },
             ];
             const pos = positions[idx % positions.length];
             const isWorking = data.status === 'working';

             return (
               <div key={name} className="absolute flex flex-col items-center justify-center transition-all duration-300" style={pos}>
                  
                  {/* 말풍선 */}
                  {isWorking && (
                    <div className="mb-2 px-3 py-1 bg-white/90 text-black text-xs font-bold rounded-lg shadow-lg relative animate-bounce z-20">
                      {data.task}
                      <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-white/90 rotate-45"></div>
                    </div>
                  )}

                  {/* 캐릭터 스프라이트 */}
                  <div className={`relative ${isWorking ? 'animate-pulse' : ''} drop-shadow-xl hover:-translate-y-1 transition-transform`}>
                    <img 
                      src={name === '코다리 부장' ? '/assets/kodari_trans.png' : '/assets/worker_trans.png'} 
                      alt={name} 
                      className="w-16 h-16 object-contain image-rendering-pixelated" 
                      style={{ imageRendering: 'pixelated' }} 
                    />
                  </div>
                  
                  {/* 이름표 */}
                  <div className="mt-1 px-2 py-0.5 bg-black/60 rounded text-[10px] text-gray-200 backdrop-blur-sm border border-white/10">
                    {name}
                  </div>
               </div>
             )
          })}
        </div>
      </div>

      {/* 2. Glassmorphism 사이드바 */}
      <div className="w-[360px] h-full glass-panel border-l flex flex-col z-20 shadow-[-10px_0_30px_rgba(0,0,0,0.5)]">
        
        {/* 상단 탭 */}
        <div className="flex border-b border-white/10">
          <button className="flex-1 py-4 text-sm font-semibold text-indigo-400 border-b-2 border-indigo-500">
            💬 AI 크루 대화망
          </button>
          <button className="flex-1 py-4 text-sm font-semibold text-gray-500 hover:text-gray-300 transition-colors">
            📚 기억 창고
          </button>
        </div>

        {/* 요원 상태 뷰어 */}
        <div className="p-4 border-b border-white/10">
          <h2 className="text-xs font-bold text-gray-400 mb-3 uppercase tracking-widest">Active Crew</h2>
          <div className="flex flex-wrap gap-2">
            {Object.entries(agents).map(([name, data]) => (
              <div key={name} className={`px-2 py-1.5 rounded-lg border text-xs font-semibold flex items-center space-x-2 transition-colors ${data.status === 'working' ? 'border-indigo-500/50 bg-indigo-500/10 text-indigo-300' : 'border-gray-500/30 bg-gray-500/10 text-gray-400'}`}>
                <div className={`w-2 h-2 rounded-full ${data.status === 'working' ? 'bg-indigo-400 animate-pulse' : 'bg-gray-500'}`}></div>
                <span>{name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* 실시간 로그 */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <div className="text-xs text-gray-500 text-center uppercase tracking-wide">-- 오늘 --</div>
          
          {Object.entries(agents).filter(([_, data]) => data.status === 'working').map(([name, data]) => (
             <div key={name} className="flex flex-col mb-3 animate-fade-in">
                <span className="text-[11px] text-gray-400 ml-1 mb-1">{name}</span>
                <div className="bg-[#1A1A24] border border-white/5 rounded-2xl rounded-tl-sm px-4 py-3 text-sm text-gray-200">
                  {data.task}
                </div>
             </div>
          ))}

          {/* 시스템 로그 */}
          <div className="text-center w-full my-2">
           <span className="bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-full px-3 py-1 text-[10px]">
             대기열이 갱신되었습니다.
           </span>
          </div>

        </div>

      </div>
    </div>
  )
}

export default App;
