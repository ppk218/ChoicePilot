import React from 'react';
import { Modal, ModalHeader, ModalTitle, ModalContent } from './Modal';

const DisclaimerModal = ({ isOpen, onClose, onConfirm, text }) => {
  if (!isOpen) return null;
  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <ModalHeader>
        <ModalTitle>Disclaimer</ModalTitle>
      </ModalHeader>
      <ModalContent>
        <p className="text-sm text-gray-700 whitespace-pre-line">{text}</p>
      </ModalContent>
      <div className="p-4 flex justify-end space-x-2 border-t">
        <button className="px-4 py-2 rounded bg-gray-100 text-gray-700" onClick={onClose}>Cancel</button>
        <button className="px-4 py-2 rounded gingee-bg-coral text-white" onClick={() => { onConfirm && onConfirm(); onClose(); }}>Continue</button>
      </div>
    </Modal>
  );
};

export default DisclaimerModal;
