import React from "react";

interface Props {
  value: number; // 0-100
}

const ProgressBar: React.FC<Props> = ({ value }) => {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div className="w-full bg-slate-700 rounded-full h-2 overflow-hidden">
      <div
        className="bg-violet-500 h-2 rounded-full transition-all duration-300"
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
};

export default ProgressBar;
