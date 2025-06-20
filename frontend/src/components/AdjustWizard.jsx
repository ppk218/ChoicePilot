import React, { useState, useEffect } from 'react';
import { Modal } from './ui/Modal';

const advisorOptions = [
  { value: 'realist', label: 'Realist' },
  { value: 'visionary', label: 'Visionary' },
  { value: 'creative', label: 'Creative' },
  { value: 'pragmatist', label: 'Pragmatist' },
  { value: 'supportive', label: 'Supportive' },
  { value: 'optimistic', label: 'Optimistic' },
  { value: 'skeptical', label: 'Skeptical' },
  { value: 'analytical', label: 'Analytical' }
];

const AdjustWizard = ({ isOpen, onClose, onApply }) => {
  const [step, setStep] = useState(1);
  const [adjustmentType, setAdjustmentType] = useState('');
  const [advisor, setAdvisor] = useState('realist');
  const [reuseQuestions, setReuseQuestions] = useState(true);

  useEffect(() => {
    if (!isOpen) {
      setStep(1);
      setAdjustmentType('');
      setAdvisor('realist');
      setReuseQuestions(true);
    }
  }, [isOpen]);

  const nextStep = () => {
    if (step === 1) {
      if (adjustmentType === 'new_persona') {
        setStep(2);
      } else {
        setStep(3);
      }
    } else if (step === 2) {
      setStep(3);
    }
  };

  const prevStep = () => {
    setStep(step - 1);
  };

  const handleApply = () => {
    onApply({ adjustmentType, advisor, reuseQuestions });
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} className="p-6">
      {step === 1 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-foreground">What would you like to change?</h3>
          <div className="space-y-3">
            <label className="flex items-center gap-3 p-3 border border-border rounded-lg cursor-pointer hover:bg-muted/50">
              <input type="radio" name="adjustType" value="edit_answers" onChange={e => setAdjustmentType(e.target.value)} className="w-4 h-4" />
              <span>Edit previous answers</span>
            </label>
            <label className="flex items-center gap-3 p-3 border border-border rounded-lg cursor-pointer hover:bg-muted/50">
              <input type="radio" name="adjustType" value="new_persona" onChange={e => setAdjustmentType(e.target.value)} className="w-4 h-4" />
              <span>Ask fresh questions with new advisor</span>
            </label>
            <label className="flex items-center gap-3 p-3 border border-border rounded-lg cursor-pointer hover:bg-muted/50">
              <input type="radio" name="adjustType" value="change_type" onChange={e => setAdjustmentType(e.target.value)} className="w-4 h-4" />
              <span>Change decision approach</span>
            </label>
          </div>
          <div className="flex justify-end gap-2 pt-4">
            <button onClick={onClose} className="px-3 py-1 border rounded">Cancel</button>
            <button onClick={nextStep} disabled={!adjustmentType} className="px-3 py-1 bg-primary text-primary-foreground rounded">Next</button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-foreground">Choose an advisor</h3>
          <select value={advisor} onChange={e => setAdvisor(e.target.value)} className="w-full border p-2 rounded">
            {advisorOptions.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          <div className="flex justify-between pt-4">
            <button onClick={prevStep} className="px-3 py-1 border rounded">Back</button>
            <button onClick={nextStep} className="px-3 py-1 bg-primary text-primary-foreground rounded">Next</button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-foreground">Follow-up questions</h3>
          <label className="flex items-center gap-3">
            <input type="radio" name="reuse" value="true" checked={reuseQuestions} onChange={() => setReuseQuestions(true)} className="w-4 h-4" />
            <span>Reuse existing questions</span>
          </label>
          <label className="flex items-center gap-3">
            <input type="radio" name="reuse" value="false" checked={!reuseQuestions} onChange={() => setReuseQuestions(false)} className="w-4 h-4" />
            <span>Generate new questions</span>
          </label>
          <div className="flex justify-between pt-4">
            {adjustmentType === 'new_persona' && (<button onClick={prevStep} className="px-3 py-1 border rounded">Back</button>)}
            <button onClick={handleApply} className="px-3 py-1 bg-primary text-primary-foreground rounded">Apply Changes</button>
          </div>
        </div>
      )}
    </Modal>
  );
};

export default AdjustWizard;
