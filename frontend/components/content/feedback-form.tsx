"use client";

import { useState } from "react";
import { submitFeedback } from "../../lib/api/content";

const ratingValues = [1, 2, 3, 4, 5] as const;

function StarIcon({ selected }: { selected: boolean }) {
  return (
    <svg className={selected ? "feedback-star feedback-star--selected" : "feedback-star"} viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path d="m12 2.8 2.84 5.76 6.36.92-4.6 4.48 1.09 6.33L12 17.3l-5.69 2.99 1.09-6.33-4.6-4.48 6.36-.92L12 2.8Z" />
    </svg>
  );
}

export function FeedbackForm({ english = false }: { english?: boolean }) {
  const t = (fa: string, en: string) => english ? en : fa;
  const [type, setType] = useState("shopping");
  const [rating, setRating] = useState("");
  const [hoveredRating, setHoveredRating] = useState(0);
  const [message, setMessage] = useState("");
  const [contact, setContact] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await submitFeedback({ feedback_type: type, rating: rating ? Number(rating) : undefined, message, contact_permission: contact });
      setSuccess(true);
    } catch {
      setError(t("ثبت بازخورد ناموفق بود.", "Feedback could not be submitted."));
    } finally {
      setBusy(false);
    }
  }

  if (success) {
    return <section role="status" className="form-success feedback-success"><h2>{t("بازخورد شما دریافت شد", "Your feedback was received")}</h2></section>;
  }

  const visibleRating = hoveredRating || Number(rating);
  return <form className="contact-form feedback-form" onSubmit={submit}>
    <h2>{t("ارسال بازخورد", "Send feedback")}</h2>
    <label>{t("نوع بازخورد", "Feedback type")}<select className="feedback-select" value={type} onChange={e => setType(e.target.value)}>
      <option value="shopping">{t("تجربه خرید", "Shopping experience")}</option>
      <option value="product">{t("محصول", "Product")}</option>
      <option value="order">{t("سفارش و تحویل", "Order experience")}</option>
      <option value="support">{t("پشتیبانی", "Support experience")}</option>
      <option value="website">{t("وب‌سایت", "Website")}</option>
      <option value="other">{t("سایر", "Other")}</option>
    </select></label>
    <fieldset className="feedback-rating-fieldset">
      <legend>{t("امتیاز اختیاری", "Optional rating")}</legend>
      <div className="feedback-rating" role="radiogroup" aria-label={t("امتیاز", "Rating")} dir="ltr" onMouseLeave={() => setHoveredRating(0)}>
        {ratingValues.map(value => <label className="feedback-star-option" key={value} onMouseEnter={() => setHoveredRating(value)}>
          <input id={`feedback-rating-${value}`} type="radio" name="rating" value={value} aria-label={english ? `${value} out of 5` : `امتیاز ${value} از ۵`} checked={rating === String(value)} onChange={e => setRating(e.target.value)} />
          <span aria-hidden="true"><StarIcon selected={visibleRating >= value} /></span>
          <span className="sr-only">{english ? `${value} out of 5` : `امتیاز ${value} از ۵`}</span>
        </label>)}
      </div>
    </fieldset>
    <label className="feedback-message-field">{t("پیام *", "Message *")}<textarea className="feedback-message" required value={message} onChange={e => setMessage(e.target.value)} /></label>
    <label className="feedback-contact-option"><input className="feedback-contact-checkbox" type="checkbox" checked={contact} onChange={e => setContact(e.target.checked)} />{t("در صورت نیاز امکان تماس وجود دارد", "Contact may be used if needed")}</label>
    {error && <p role="alert" className="form-error">{error}</p>}
    <button className="btn-primary feedback-submit" disabled={busy}>{busy ? t("در حال ارسال…", "Submitting…") : t("ارسال بازخورد", "Submit Feedback")}</button>
  </form>;
}
