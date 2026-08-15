export function CheckoutProgress({ hasItems, customerComplete }: { hasItems: boolean; customerComplete: boolean }) {
  const steps = [
    { key: "cart", label: "سبد خرید", description: "بررسی کالاها", complete: hasItems, current: !customerComplete },
    { key: "details", label: "اطلاعات سفارش", description: "اطلاعات مشتری و تحویل", complete: customerComplete, current: customerComplete },
    { key: "payment", label: "پرداخت", description: "انتقال به درگاه پرداخت", complete: false, current: false },
  ];
  return <nav className="checkout-progress" aria-label="مراحل ثبت سفارش"><ol>{steps.map((step, index) => <li className={step.current ? "is-current" : step.complete ? "is-complete" : ""} key={step.key}><span className="checkout-progress-marker" aria-hidden="true">{step.complete ? "✓" : index + 1}</span><span><b>{step.label}</b><small>{step.description}</small></span></li>)}</ol></nav>;
}
