import React, { useRef, useState } from 'react';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'glass' | 'gradient';
  style?: React.CSSProperties;
}

const GlassCard: React.FC<GlassCardProps> = ({ 
  children, 
  className = '', 
  variant = 'default',
  style
}) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    setMousePosition({ x, y });
  };

  const getVariantClasses = () => {
    switch (variant) {
      case 'glass':
        return 'backdrop-blur-xl bg-white/[0.03]';
      case 'gradient':
        return 'before:absolute before:inset-0 before:rounded-2xl before:bg-gradient-to-br before:from-accent/5 before:to-transparent before:opacity-0 hover:before:opacity-100 before:transition-opacity before:duration-500';
      default:
        return '';
    }
  };

  return (
    <div 
      ref={cardRef}
      className={`
        relative glass-card overflow-hidden
        ${getVariantClasses()}
        ${className}
      `}
      style={style}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Mouse-tracking spotlight effect */}
      {isHovered && (
        <div 
          className="absolute pointer-events-none mix-blend-screen"
          style={{
            width: '300px',
            height: '300px',
            background: 'radial-gradient(circle, rgba(94,106,210,0.15) 0%, transparent 70%)',
            left: mousePosition.x - 150,
            top: mousePosition.y - 150,
            opacity: isHovered ? 1 : 0,
            transition: 'opacity 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
          }}
        />
      )}
      
      {/* Inner highlight line */}
      <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-white/10 to-transparent" />
      
      {/* Content */}
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
};

export default GlassCard;
