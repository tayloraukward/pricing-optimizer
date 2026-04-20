import React, { useEffect, useRef } from 'react';

interface MousePosition {
  x: number;
  y: number;
}

const AmbientBackground: React.FC = () => {
  const mousePosition = useRef<MousePosition>({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      mousePosition.current = { x: e.clientX, y: e.clientY };
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none">
      {/* Layer 1: Base gradient */}
      <div className="absolute inset-0 bg-gradient-radial" />
      
      {/* Layer 2: Noise texture */}
      <div 
        className="absolute inset-0 opacity-[0.015]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
        }}
      />
      
      {/* Layer 3: Animated gradient blobs */}
      <div className="absolute inset-0">
        {/* Primary blob - top center */}
        <div 
          className="absolute top-0 left-1/2 -translate-x-1/2 w-[900px] h-[1400px] bg-accent/25 rounded-full blur-[150px] animate-float"
          style={{
            animationDuration: '10s',
          }}
        />
        
        {/* Secondary blob - left side */}
        <div 
          className="absolute top-1/4 left-0 w-[600px] h-[800px] bg-purple-500/15 rounded-full blur-[120px] animate-float"
          style={{
            animationDuration: '8s',
            animationDelay: '2s',
          }}
        />
        
        {/* Tertiary blob - right side */}
        <div 
          className="absolute top-1/3 right-0 w-[500px] h-[700px] bg-indigo-500/12 rounded-full blur-[100px] animate-float"
          style={{
            animationDuration: '9s',
            animationDelay: '4s',
          }}
        />
        
        {/* Bottom accent blob */}
        <div 
          className="absolute bottom-0 left-1/3 w-[400px] h-[600px] bg-accent/10 rounded-full blur-[80px] animate-float"
          style={{
            animationDuration: '7s',
            animationDelay: '1s',
          }}
        />
      </div>
      
      {/* Layer 4: Grid overlay */}
      <div 
        className="absolute inset-0 opacity-[0.02]"
        style={{
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)
          `,
          backgroundSize: '64px 64px',
        }}
      />
      
      {/* Layer 5: Mouse-tracking spotlight */}
      <div 
        className="absolute w-[300px] h-[300px] rounded-full pointer-events-none mix-blend-screen"
        style={{
          background: 'radial-gradient(circle, rgba(94,106,210,0.15) 0%, transparent 70%)',
          left: mousePosition.current.x - 150,
          top: mousePosition.current.y - 150,
          transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
        }}
      />
    </div>
  );
};

export default AmbientBackground;
